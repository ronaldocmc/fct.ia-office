"""Deterministic draft-only capabilities; no external calls or LLM."""
import argparse
import json
from pathlib import Path

def required(data, key):
    value = data.get(key)
    if not isinstance(value,str) or not value.strip() or len(value)>4000:
        raise ValueError("Campo inválido: "+key)
    return value.strip()

def execute(skill, data):
    if data.get("synthetic") is not True:
        raise ValueError("Somente dados fictícios")
    if skill == "minuta_oficio":
        body = "OFÍCIO EXPERIMENTAL\nDestinatário: "+required(data,"destinatario")+"\nAssunto: "+required(data,"assunto")+"\n"+required(data,"texto")
    elif skill == "briefing":
        items = data.get("itens")
        if not isinstance(items,list) or not all(isinstance(x,str) and len(x)<=1000 for x in items) or len(items)>50:
            raise ValueError("Lista de itens inválida")
        body = "BRIEFING EXPERIMENTAL\n"+"\n".join("- "+x for x in items)
    elif skill == "classificar_solicitacao":
        text = required(data,"descricao").casefold()
        categories = {"infraestrutura":("energia","elétrica","vazamento"),"tecnologia":("computador","rede","internet")}
        category = next((k for k, words in categories.items() if any(w in text for w in words)), "triagem humana")
        body = "Categoria sugerida: "+category
    else:
        raise ValueError("Skill não autorizada")
    return {"skill":skill,"status":"draft","requires_human_review":True,"external_action":False,"result":body}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("skill",choices=["minuta_oficio","briefing","classificar_solicitacao"])
    p.add_argument("input",type=Path)
    a=p.parse_args()
    if a.input.stat().st_size>64000:
        p.error("Arquivo excede limite")
    print(json.dumps(execute(a.skill,json.loads(a.input.read_text(encoding="utf-8"))),ensure_ascii=False))
if __name__=="__main__":
    main()
