import requests
from . import config as C

class Odoo:
    def __init__(self):
        missing = [k for k, v in {
            "ODOO_URL": C.ODOO_URL, "ODOO_DB": C.ODOO_DB,
            "ODOO_USER": C.ODOO_USER, "ODOO_API_KEY": C.ODOO_API_KEY,
        }.items() if not v]
        if missing:
            raise RuntimeError("Faltan secrets de Odoo: " + ", ".join(missing))
        self.url, self.db, self.user, self.key = C.ODOO_URL, C.ODOO_DB, C.ODOO_USER, C.ODOO_API_KEY
        self.uid = self._call("common", "authenticate", [self.db, self.user, self.key, {}])

    def _call(self, service, method, args):
        payload = {"jsonrpc":"2.0","method":"call","params":{"service":service,"method":method,"args":args},"id":1}
        r = requests.post(f"{self.url}/jsonrpc", json=payload, timeout=C.REQUEST_TIMEOUT)
        r.raise_for_status()
        data = r.json()
        if data.get("error"):
            raise RuntimeError(str(data["error"]))
        return data.get("result")

    def call(self, model, method, *args, **kwargs):
        return self._call("object", "execute_kw",
                          [self.db, self.uid, self.key, model, method, list(args), kwargs])

    def test(self):
        if not self.uid:
            raise RuntimeError("Odoo no autenticó")
        return self.call("res.users", "read", [self.uid], fields=["name", "login"])

    def buscar_lead_email(self, email):
        # Solo reutilizar leads de Pase 360 o sin empresa asignada.
        # Evita tomar un lead de Distribuidora Santiago por compartir la base.
        domain = [
            ["email_from", "=", email],
            ["company_id", "in", [False, C.ODOO_COMPANY_ID]],
        ]
        ids = self.call("crm.lead", "search", domain, limit=1)
        return ids[0] if ids else None

    def crear_lead(self, c):
        vals = {
            "name": f"[{c['tipo']}] {c['name']}",
            "partner_name": c["name"],
            "email_from": c["email"],
            "phone": c.get("phone") or False,
            "street": c.get("direccion") or False,
            "city": "Córdoba",
            "company_id": C.ODOO_COMPANY_ID,
            "description": f"Origen: {c.get('source','')} | Email: {c.get('email_source','')} | Web: {c.get('website','')}",
        }
        return self.call("crm.lead", "create", vals)

    def enviar(self, para, asunto, cuerpo, lead_id=None):
        vals = {
            "subject": asunto, "body_html": cuerpo, "email_to": para,
            "email_from": C.SENDER_EMAIL, "auto_delete": True,
        }
        if lead_id:
            vals.update({"res_id": lead_id, "model": "crm.lead"})
        mail_id = self.call("mail.mail", "create", vals)
        self.call("mail.mail", "send", [mail_id], force_send=True)
        state = self.call("mail.mail", "read", [mail_id], fields=["state","failure_reason"])
        return {"mail_id": mail_id, "state": state}
