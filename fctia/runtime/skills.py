"""Deterministic draft-only capabilities; no external calls or LLM."""
import argparse
import json
from pathlib import Path

def required(data, key):
    value = data.get(key)
    if not isinstance(value,str) or not value.strip() or len(value)>4000:
        raise ValueError("Campo inválido: "+key)
    return value.strip()

def items(data, key):
    value = data.get(key)
    if not isinstance(value, list) or not value or len(value) > 50 or not all(isinstance(x, str) and x.strip() and len(x) <= 1000 for x in value):
        raise ValueError("Lista inválida: " + key)
    return "\n".join("- " + x.strip() for x in value)

SKILLS = (
    "planejamento", "delegacao", "revisao", "agenda_simulada", "briefing",
    "minuta_email", "minuta_oficio", "minuta_ata", "relatorio",
    "classificar_solicitacao", "propor_ordem", "acompanhar_prazo",
)

def execute(skill, data):
    if data.get("synthetic") is not True:
        raise ValueError("Somente dados fictícios")
    if skill == "minuta_oficio":
        body = "OFÍCIO EXPERIMENTAL\nDestinatário: "+required(data,"destinatario")+"\nAssunto: "+required(data,"assunto")+"\n"+required(data,"texto")
    elif skill == "briefing":
        briefing_items = data.get("itens")
        if not isinstance(briefing_items,list) or not all(isinstance(x,str) and len(x)<=1000 for x in briefing_items) or len(briefing_items)>50:
            raise ValueError("Lista de itens inválida")
        body = "BRIEFING EXPERIMENTAL\n"+"\n".join("- "+x for x in briefing_items)
    elif skill == "classificar_solicitacao":
        text = required(data,"descricao").casefold()
        categories = {"infraestrutura":("energia","elétrica","vazamento"),"tecnologia":("computador","rede","internet")}
        category = next((k for k, words in categories.items() if any(w in text for w in words)), "triagem humana")
        body = "Categoria sugerida: "+category
    elif skill == "planejamento":
        body = "PLANO EXPERIMENTAL\nObjetivo: " + required(data,"objetivo") + "\nEtapas propostas:\n" + items(data,"etapas")
    elif skill == "delegacao":
        body = "DELEGAÇÃO PROPOSTA\nResponsável: " + required(data,"responsavel") + "\nAtividade: " + required(data,"atividade")
    elif skill == "revisao":
        body = "REVISÃO PENDENTE\nEntregável: " + required(data,"entregavel") + "\nCritérios para verificação humana:\n" + items(data,"criterios")
    elif skill == "agenda_simulada":
        body = "AGENDA EXPERIMENTAL\n" + items(data,"compromissos")
    elif skill == "minuta_email":
        body = "MINUTA — NÃO ENVIADA\nPara: " + required(data,"destinatario") + "\nAssunto: " + required(data,"assunto") + "\n" + required(data,"texto")
    elif skill == "minuta_ata":
        body = "ATA EXPERIMENTAL\nReunião: " + required(data,"reuniao") + "\nPautas:\n" + items(data,"pautas") + "\nDeliberações propostas:\n" + items(data,"deliberacoes")
    elif skill == "relatorio":
        body = "RELATÓRIO EXPERIMENTAL\nTítulo: " + required(data,"titulo") + "\nObservações:\n" + items(data,"observacoes")
    elif skill == "propor_ordem":
        body = "ORDEM DE SERVIÇO PROPOSTA\nSolicitação: " + required(data,"descricao") + "\nSetor sugerido: " + required(data,"setor")
    elif skill == "acompanhar_prazo":
        from datetime import date
        deadline = date.fromisoformat(required(data,"prazo"))
        reference = date.fromisoformat(required(data,"referencia"))
        delta = (deadline-reference).days
        body = "ACOMPANHAMENTO EXPERIMENTAL\n" + required(data,"atividade") + "\n" + ("Vencido há " + str(-delta) + " dia(s)" if delta < 0 else "Restam " + str(delta) + " dia(s)")
    else:
        raise ValueError("Skill não autorizada")
    return {"skill":skill,"status":"draft","requires_human_review":True,"external_action":False,"result":body}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("skill",choices=SKILLS)
    p.add_argument("input",type=Path)
    a=p.parse_args()
    if a.input.stat().st_size>64000:
        p.error("Arquivo excede limite")
    print(json.dumps(execute(a.skill,json.loads(a.input.read_text(encoding="utf-8"))),ensure_ascii=False))
if __name__=="__main__":
    main()
