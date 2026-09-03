#!/usr/bin/env python3
"""
fp.py — client CLI minimal pour l'API Facturation.PRO (https://www.facturation.pro/).

Dépendances : Python 3.8+, bibliothèque standard uniquement.

Configuration (variables d'environnement, ou fichier ~/.config/facturation-pro/config.env) :
  FACTURATION_API_ID      identifiant API           (obligatoire)
  FACTURATION_API_KEY     clé API                   (obligatoire)
  FACTURATION_FIRM_ID     identifiant entreprise    (obligatoire, sauf `account`)
  FACTURATION_USER_AGENT  ex: "MonApp (moi@exemple.fr)"  (recommandé par l'éditeur)

Exemples :
  fp.py account
  fp.py get customers -p company=acme
  fp.py get invoices -p bill_type=unpaid --all --fields id,invoice_ref,customer_name,total_with_vat,term_on --sum total_with_vat
  fp.py get quotes/123
  fp.py post quotes -d '{"customer_id":1,"title":"Site web","items":[{"position":1,"title":"Dev","quantity":"1","unit_price":"1500","vat":"0.200"}]}'
  fp.py post invoices -p type_doc=draft -d @facture.json
  fp.py patch invoices/456 -p type_doc=final -d '{}' --yes
  fp.py patch invoices/456 -d '{"paid_on":"2026-09-03","payment_mode":3}'
  fp.py post quotes/123/invoice --yes
  fp.py pdf invoices 456 -o facture.pdf
  fp.py upload purchases 789 ./ticket.pdf --filename ticket-2026-09.pdf
  fp.py delete quotes/123 --yes

Les chemins relatifs sont préfixés par /firms/FIRM_ID/ et suffixés par .json.
Un chemin commençant par "/" est utilisé tel quel (ex: /account.json).
"""
import argparse
import base64
import json
import mimetypes
import os
import sys
import time
import uuid
from urllib import error, parse, request

BASE = "https://www.facturation.pro"
CONFIG_FILE = os.path.expanduser("~/.config/facturation-pro/config.env")
DEFAULT_UA = "facturation-pro-skill/1.0 (Claude Code; contact non renseigne)"
PAGE_DELAY = 0.6  # ~2 req/s max autorisées


# --------------------------------------------------------------------------- config
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip()
                if k.startswith("export "):
                    k = k[7:].strip()
                v = v.strip().strip('"').strip("'")
                os.environ.setdefault(k, v)
    cfg = {
        "api_id": os.environ.get("FACTURATION_API_ID"),
        "api_key": os.environ.get("FACTURATION_API_KEY"),
        "firm_id": os.environ.get("FACTURATION_FIRM_ID"),
        "user_agent": os.environ.get("FACTURATION_USER_AGENT") or DEFAULT_UA,
    }
    return cfg


def require(cfg, need_firm=True, dry_run=False):
    missing = [k for k in ("api_id", "api_key") if not cfg[k]]
    if need_firm and not cfg["firm_id"]:
        missing.append("firm_id")
    if missing and not dry_run:
        names = {"api_id": "FACTURATION_API_ID", "api_key": "FACTURATION_API_KEY", "firm_id": "FACTURATION_FIRM_ID"}
        sys.stderr.write(
            "Configuration manquante : " + ", ".join(names[m] for m in missing) + "\n"
            "Renseigne ces variables d'environnement ou le fichier " + CONFIG_FILE + "\n"
            "(clés disponibles sur https://www.facturation.pro/account/api). "
            "Utilise `fp.py account` pour lister tes FIRM_ID.\n"
        )
        sys.exit(2)
    if cfg["user_agent"] == DEFAULT_UA and not dry_run:
        sys.stderr.write("Avertissement : FACTURATION_USER_AGENT non défini. L'éditeur demande un User-Agent avec un contact.\n")


# --------------------------------------------------------------------------- url
def build_url(cfg, path, params=None):
    if path.startswith("http"):
        url = path
    elif path.startswith("/"):
        url = BASE + path
    else:
        url = f"{BASE}/firms/{cfg['firm_id'] or 'FIRM_ID'}/{path.lstrip('/')}"
    base, _, query = url.partition("?")
    if not (base.endswith(".json") or base.endswith(".pdf")):
        base += ".json"
    qs = dict(parse.parse_qsl(query, keep_blank_values=True))
    if params:
        qs.update(params)
    if qs:
        base += "?" + parse.urlencode(qs)
    return base


def parse_params(pairs):
    out = {}
    for p in pairs or []:
        if "=" not in p:
            sys.exit(f"Paramètre invalide (attendu cle=valeur) : {p}")
        k, v = p.split("=", 1)
        out[k] = v
    return out


def load_body(data):
    if data is None:
        return None
    if data.startswith("@"):
        with open(data[1:], encoding="utf-8") as fh:
            data = fh.read()
    try:
        return json.loads(data)
    except json.JSONDecodeError as e:
        sys.exit(f"JSON invalide dans -d : {e}")


# --------------------------------------------------------------------------- http
def multipart(fields, file_field, filepath, filename=None):
    boundary = "----fp" + uuid.uuid4().hex
    body = bytearray()
    for k, v in (fields or {}).items():
        body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode()
    fname = filename or os.path.basename(filepath)
    ctype = mimetypes.guess_type(fname)[0] or "application/octet-stream"
    with open(filepath, "rb") as fh:
        content = fh.read()
    body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"{file_field}\"; filename=\"{fname}\"\r\nContent-Type: {ctype}\r\n\r\n".encode()
    body += content + f"\r\n--{boundary}--\r\n".encode()
    return bytes(body), f"multipart/form-data; boundary={boundary}"


def call(cfg, method, url, body=None, raw_body=None, content_type=None, accept="application/json", retries=3, dry_run=False):
    token = base64.b64encode(f"{cfg['api_id']}:{cfg['api_key']}".encode()).decode()
    headers = {"Authorization": f"Basic {token}", "User-Agent": cfg["user_agent"], "Accept": accept}
    data = None
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json; charset=utf-8"
    elif raw_body is not None:
        data = raw_body
        headers["Content-Type"] = content_type
    if dry_run:
        shown = dict(headers)
        shown["Authorization"] = "Basic ***"
        print(json.dumps({"dry_run": True, "method": method, "url": url, "headers": shown,
                          "body": body if body is not None else (f"<{len(data)} octets multipart>" if data else None)},
                         ensure_ascii=False, indent=2))
        sys.exit(0)
    for attempt in range(retries + 1):
        req = request.Request(url, data=data, headers=headers, method=method)
        try:
            with request.urlopen(req, timeout=90) as resp:
                return resp.status, dict(resp.headers), resp.read()
        except error.HTTPError as e:
            if e.code == 429 and attempt < retries:
                wait = int(e.headers.get("Retry-After", "10") or 10)
                sys.stderr.write(f"Quota atteint (429), attente {wait}s…\n")
                time.sleep(wait)
                continue
            if e.code >= 500 and attempt < retries:
                time.sleep(2 ** attempt)
                continue
            return e.code, dict(e.headers), e.read()
        except (error.URLError, TimeoutError) as e:
            if attempt < retries:
                time.sleep(2 ** attempt)
                continue
            sys.exit(f"Erreur réseau : {e}")


def decode(content):
    text = content.decode("utf-8", errors="replace") if content else ""
    try:
        return json.loads(text) if text.strip() else None
    except json.JSONDecodeError:
        return text


def fail(status, headers, content):
    payload = decode(content)
    sys.stderr.write(json.dumps({"error": True, "status": status, "message": headers.get("Status") or "", "body": payload},
                                ensure_ascii=False, indent=2) + "\n")
    hints = {
        400: "Données mal formatées (JSON ou en-têtes). Vérifie le corps envoyé.",
        401: "Authentification refusée : vérifie FACTURATION_API_ID / FACTURATION_API_KEY.",
        403: "Accès interdit (ex: données SEPA sans clé administrateur, ou FIRM_ID d'une autre entreprise).",
        404: "Enregistrement introuvable : vérifie l'ID et le FIRM_ID.",
        422: "Validation refusée : lis le champ 'errors' ci-dessus (ex: facture finalisée non modifiable, client déjà facturé).",
        429: "Quota dépassé (600 req / 5 min, 10 000 / jour).",
        501: "Content-Type manquant ou incorrect.",
    }
    if status in hints:
        sys.stderr.write("Indice : " + hints[status] + "\n")
    sys.exit(1)


# --------------------------------------------------------------------------- output helpers
def pick_fields(payload, fields):
    if not fields:
        return payload
    keys = [f.strip() for f in fields.split(",") if f.strip()]

    def trim(obj):
        return {k: obj.get(k) for k in keys} if isinstance(obj, dict) else obj

    if isinstance(payload, list):
        return [trim(o) for o in payload]
    return trim(payload)


def emit(payload, compact=False):
    if isinstance(payload, (dict, list)):
        print(json.dumps(payload, ensure_ascii=False, indent=None if compact else 2))
    elif payload is not None:
        print(payload)


def to_number(v):
    try:
        return float(str(v).replace(",", "."))
    except (TypeError, ValueError):
        return 0.0


# --------------------------------------------------------------------------- dangerous ops guard
def is_dangerous(method, url):
    path = url.split("?")[0]
    query = url.split("?")[1] if "?" in url else ""
    if method == "DELETE":
        return "suppression définitive (aucune corbeille côté API)"
    if method == "POST":
        if path.endswith("/refund.json"):
            return "création d'un avoir (numéroté, irréversible)"
        if path.endswith("/invoice.json"):
            return "conversion du devis en facture finalisée et numérotée"
        if path.endswith("/emails.json"):
            return "envoi d'un courriel au client"
        if path.endswith("/invoices.json") and "type_doc=draft" not in query and "external=1" not in query:
            return "création d'une facture FINALISÉE et numérotée (ajoute -p type_doc=draft pour un brouillon)"
    if method == "PATCH" and "type_doc=final" in query:
        return "finalisation d'une facture (numérotation légale, montants ensuite immuables)"
    return None


def guard(method, url, yes):
    reason = is_dangerous(method, url)
    if reason and not yes:
        sys.stderr.write(
            f"Opération sensible refusée sans --yes : {reason}.\n"
            "Obtiens la confirmation explicite de l'utilisateur, puis relance avec --yes.\n"
        )
        sys.exit(3)


# --------------------------------------------------------------------------- commands
def cmd_account(cfg, args):
    require(cfg, need_firm=False, dry_run=args.dry_run)
    status, headers, content = call(cfg, "GET", BASE + "/account.json", dry_run=args.dry_run)
    if status >= 400:
        fail(status, headers, content)
    emit(decode(content), args.compact)


def cmd_get(cfg, args):
    require(cfg, dry_run=args.dry_run)
    params = parse_params(args.param)
    url = build_url(cfg, args.path, params)
    status, headers, content = call(cfg, "GET", url, dry_run=args.dry_run)
    if status >= 400:
        fail(status, headers, content)
    payload = decode(content)
    pagination = None
    if headers.get("X-Pagination"):
        try:
            pagination = json.loads(headers["X-Pagination"])
        except json.JSONDecodeError:
            pagination = None
    if args.all and pagination and isinstance(payload, list):
        total_pages = int(pagination.get("total_pages", 1))
        for page in range(2, total_pages + 1):
            time.sleep(PAGE_DELAY)
            p = dict(params)
            p["page"] = str(page)
            st, hd, ct = call(cfg, "GET", build_url(cfg, args.path, p))
            if st >= 400:
                fail(st, hd, ct)
            more = decode(ct)
            if isinstance(more, list):
                payload.extend(more)
    elif pagination and int(pagination.get("total_pages", 1)) > 1 and not args.all:
        sys.stderr.write(f"Pagination : {json.dumps(pagination)} — ajoute --all pour tout récupérer ou -p page=N.\n")
    payload = pick_fields(payload, args.fields)
    emit(payload, args.compact)
    if args.sum and isinstance(payload, list):
        total = sum(to_number(o.get(args.sum)) for o in payload if isinstance(o, dict))
        sys.stderr.write(json.dumps({"count": len(payload), f"sum_{args.sum}": round(total, 2)}) + "\n")


def cmd_write(cfg, args, method):
    require(cfg, dry_run=args.dry_run)
    params = parse_params(args.param)
    url = build_url(cfg, args.path, params)
    guard(method, url, args.yes)
    body = load_body(args.data)
    if method in ("POST", "PATCH") and body is None:
        body = {}
    status, headers, content = call(cfg, method, url, body=body, dry_run=args.dry_run)
    if status >= 400:
        fail(status, headers, content)
    payload = decode(content)
    if headers.get("Location"):
        sys.stderr.write(f"Location: {headers['Location']}\n")
    emit(pick_fields(payload, args.fields), args.compact)
    if payload is None:
        sys.stderr.write(f"OK ({status})\n")


def cmd_pdf(cfg, args):
    require(cfg, dry_run=args.dry_run)
    params = {}
    if args.proforma:
        params["proforma"] = "1"
    if args.original:
        params["original"] = "1"
    url = build_url(cfg, f"{args.kind}/{args.id}.pdf", params)
    status, headers, content = call(cfg, "GET", url, accept="application/pdf", dry_run=args.dry_run)
    if status >= 400:
        fail(status, headers, content)
    out = args.output or f"{args.kind[:-1]}-{args.id}.pdf"
    with open(out, "wb") as fh:
        fh.write(content)
    print(json.dumps({"saved": os.path.abspath(out), "bytes": len(content)}))


def cmd_upload(cfg, args):
    require(cfg, dry_run=args.dry_run)
    if not os.path.isfile(args.file):
        sys.exit(f"Fichier introuvable : {args.file}")
    params = {}
    if args.filename:
        params["filename"] = args.filename
    if args.visible:
        params["visible"] = "1"
    url = build_url(cfg, f"{args.kind}/{args.id}/upload", params)
    raw, ctype = multipart({}, "upload_file", args.file, args.filename)
    status, headers, content = call(cfg, "POST", url, raw_body=raw, content_type=ctype, dry_run=args.dry_run)
    if status >= 400:
        fail(status, headers, content)
    emit(decode(content), args.compact)


# --------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description="Client CLI pour l'API Facturation.PRO", formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    ap.add_argument("--dry-run", action="store_true", help="affiche la requête sans l'envoyer")
    ap.add_argument("--compact", action="store_true", help="JSON sur une ligne")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("account", help="GET /account.json : compte et liste des FIRM_ID")

    g = sub.add_parser("get", help="GET sur une ressource (liste ou détail)")
    g.add_argument("path", help="ex: customers, invoices/123, quotes")
    g.add_argument("-p", "--param", action="append", help="paramètre de requête cle=valeur (répétable)")
    g.add_argument("--all", action="store_true", help="suit la pagination X-Pagination et concatène toutes les pages")
    g.add_argument("--fields", help="ne garde que ces champs (séparés par des virgules)")
    g.add_argument("--sum", metavar="FIELD", help="affiche la somme d'un champ numérique sur la liste (stderr)")

    for name, help_ in (("post", "POST (création / action)"), ("patch", "PATCH (mise à jour partielle)")):
        w = sub.add_parser(name, help=help_)
        w.add_argument("path")
        w.add_argument("-p", "--param", action="append", help="paramètre d'URL cle=valeur (ex: type_doc=draft)")
        w.add_argument("-d", "--data", help="corps JSON, ou @fichier.json")
        w.add_argument("--fields")
        w.add_argument("--yes", action="store_true", help="confirme une opération sensible (facture finale, avoir, envoi mail…)")

    d = sub.add_parser("delete", help="DELETE (nécessite --yes)")
    d.add_argument("path")
    d.add_argument("-p", "--param", action="append")
    d.add_argument("--fields")
    d.add_argument("--yes", action="store_true")

    p = sub.add_parser("pdf", help="télécharge le PDF d'un devis ou d'une facture")
    p.add_argument("kind", choices=["quotes", "invoices"])
    p.add_argument("id")
    p.add_argument("-o", "--output")
    p.add_argument("--proforma", action="store_true", help="devis en facture pro-forma")
    p.add_argument("--original", action="store_true", help="facture originale sans mention de règlement")

    u = sub.add_parser("upload", help="joint un fichier à un client / devis / facture / achat")
    u.add_argument("kind", choices=["customers", "quotes", "invoices", "purchases"])
    u.add_argument("id")
    u.add_argument("file")
    u.add_argument("--filename")
    u.add_argument("--visible", action="store_true", help="visible par le client (devis/factures)")

    args = ap.parse_args()
    cfg = load_config()
    if args.cmd == "account":
        cmd_account(cfg, args)
    elif args.cmd == "get":
        cmd_get(cfg, args)
    elif args.cmd == "post":
        cmd_write(cfg, args, "POST")
    elif args.cmd == "patch":
        cmd_write(cfg, args, "PATCH")
    elif args.cmd == "delete":
        args.data = None
        cmd_write(cfg, args, "DELETE")
    elif args.cmd == "pdf":
        cmd_pdf(cfg, args)
    elif args.cmd == "upload":
        cmd_upload(cfg, args)


if __name__ == "__main__":
    main()
