import argparse
import json
from . import engine

def main(argv=None):
    p = argparse.ArgumentParser(description="Agente Pase 360")
    p.add_argument("accion", choices=["diagnostico","captar","preguntas","seguimiento","reporte"])
    args = p.parse_args(argv)
    result = {
        "diagnostico":engine.diagnostico,
        "captar":engine.capturar,
        "preguntas":engine.preguntas,
        "seguimiento":engine.seguimiento,
        "reporte":engine.reporte,
    }[args.accion]()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
