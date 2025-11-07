from dotenv import load_dotenv
import os
import requests
import logging
import time
load_dotenv()

logger = logging.getLogger(__name__)

class OrchestratorAPIClient:
    def __init__(self):
        self.archimedes_host = os.getenv("ARCHIMEDES_API_HOST")
        self.headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
        self.max_retries = 3
        self.retry_delay_seconds = 5
        self.timeout = 10
        self.current_job_id = None


    
    def _make_request(self, method, endpoint, data=None):
        """Método helper para fazer requisições HTTP com re-tentativas."""
        url = f"{self.archimedes_host}/api/{endpoint.lstrip('/')}" 

        for attempt in range(self.max_retries):
            try:
                if method == 'GET':
                    response = requests.get(url, headers=self.headers, timeout=self.timeout)
                elif method == 'POST':
                    response = requests.post(url, headers=self.headers, json=data, timeout=self.timeout)
                elif method == 'PATCH':
                    response = requests.patch(url, headers=self.headers, json=data, timeout=self.timeout)
                elif method == 'PUT': # Adicione PUT se ainda não tiver
                    response = requests.put(url, headers=self.headers, json=data, timeout=self.timeout)
                else:
                    raise ValueError(f"Método HTTP não suportado: {method}")

                response.raise_for_status()
                return response.json()
            except requests.exceptions.Timeout:
                logger.error(f"Timeout ao conectar a {url} (Tentativa {attempt + 1}/{self.max_retries})")
            except requests.exceptions.ConnectionError as e:
                logger.error(f"Erro de conexão com {url}: {e} (Tentativa {attempt + 1}/{self.max_retries})")
            except requests.exceptions.RequestException as e:
                logger.error(f"Erro na requisição para {url}: {e} (Tentativa {attempt + 1}/{self.max_retries}). Resposta: {e.response.text if e.response else 'N/A'}")
            except Exception as e:
                logger.error(f"Erro inesperado ao fazer requisição para {url}: {e} (Tentativa {attempt + 1}/{self.max_retries})", exc_info=True)

            if attempt < self.max_retries - 1:
                time.sleep(self.retry_delay_seconds)

        logger.error(f"Falha em todas as {self.max_retries} tentativas para {url}. Retornando None.")
        return None

    def get_jobs_runnig(self, uuid_client=None, uuid_agent=None):
        """
        Busca o job atualmente em status 'running' para o agente configurado nesta instância.
        Retorna os detalhes do job (incluindo o ID) ou None.
        """
        print('v: ', f"jobs/running/{uuid_agent}")
        response_data = self._make_request('GET', f"jobs/running/{uuid_agent}")
        print('Se vai saber', response_data)

        if response_data['id']:
            self.current_job_id = response_data['id']

            logger.info(f"Job em execução encontrado: ID {self.current_job_id}")
            print('ID do Job Ativo:', self.current_job_id) 
            return response_data
        
    
    def create_sub_task(self, name, initial_status='running', uuid_agent=None):
        """
        Cria uma nova subtarefa para o job ativo atualmente gerenciado pela instância.
        """
        self.get_jobs_runnig(uuid_agent=uuid_agent)
        if not self.current_job_id:
            logger.error("Nenhum Job ID ativo definido nesta instância. Chame get_running_job_for_agent() primeiro.")
            return None
        payload = {
            'name': name,
            'status': initial_status,
        }

        logger.info(f"Criando subtarefa '{name}' para Job ID: {self.current_job_id}...")
        response = self._make_request('POST', f"sub-task/jobs/{self.current_job_id}", payload)
        print('respos: ', response)
        

a = OrchestratorAPIClient()
a.create_sub_task(name='task-110', uuid_agent='025dc394-b600-445b-bc34-453d0735c767')
