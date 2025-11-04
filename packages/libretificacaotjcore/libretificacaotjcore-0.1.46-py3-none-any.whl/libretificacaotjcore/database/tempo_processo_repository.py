from datetime import datetime
from pymongo.errors import BulkWriteError

class TempoProcessoRepository:
    def __init__(self, db):
        self.__db = db

    async def inserir_processo(self, processo: dict) -> bool:
        try:
            processo_no_db = await self.__db.tempo_processos.find_one(
                {"solicitacaoId": processo["solicitacaoId"], "fase": processo["fase"], "data_inicio": processo["data_inicio"], "data_fim": processo["data_fim"]}
            )

            if processo_no_db is None:
                await self.__db.tempo_processos.insert_one(processo)
                return True

            await self.__db.tempo_processos.delete_one(
                {"solicitacaoId": processo["solicitacaoId"], "fase": processo["fase"], "data_inicio": processo["data_inicio"], "data_fim": processo["data_fim"]}
            )

            processo['inicio_processo'] = datetime.now()
            await self.__db.tempo_processos.insert_one(processo)
            return True
        except Exception as e:
            print(f"❌ Erro ao inserir o processo: {e}")
            return False
        
    async def atualizar_processo(self, *, solicitacaoId: int, fase: int, data_inicio: str, data_fim: str) -> bool:
        try:
            processo_no_db = await self.__db.tempo_processos.find_one(
                {"solicitacaoId": solicitacaoId, "fase": fase, "data_inicio": data_inicio, "data_fim": data_fim}
            )

            if processo_no_db is None:
                return False
            
            processo_no_db['fim_processo'] = datetime.now()
            tempo_de_processo = self._tempo_de_processo(processo_no_db['inicio_processo'], processo_no_db['fim_processo'])
            processo_no_db['tempo_de_processo'] = tempo_de_processo

            await self.__db.tempo_processos.replace_one(
                {"solicitacaoId": solicitacaoId, "fase": fase, "data_inicio": data_inicio, "data_fim": data_fim},
                processo_no_db
            )
            return True
        except Exception as e:
            print(f"❌ Erro ao atualizar o processo: {e}")
            return False
        
    def _tempo_de_processo(self, tempo_inicio: datetime, tempo_fim: datetime) -> str | None:
        if tempo_inicio:
                delta = tempo_inicio - tempo_fim
                total_segundos = int(delta.total_seconds())

                horas = total_segundos // 3600
                minutos = (total_segundos % 3600) // 60
                segundos = total_segundos % 60

                tempo_formatado = f"{horas:02d}:{minutos:02d}:{segundos:02d}"
                return tempo_formatado
         
        return None
