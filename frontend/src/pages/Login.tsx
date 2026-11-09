import {FormEvent, useState} from "react";

export function Login() {
  const [saved, setSaved] = useState(localStorage.getItem("creditrisk.roles") ?? "analyst,policy_admin");
  const submit = (event: FormEvent<HTMLFormElement>) => { event.preventDefault(); const roles = String(new FormData(event.currentTarget).get("roles")); localStorage.setItem("creditrisk.roles", roles); setSaved(roles); };
  return <><h2>Login and local role simulation</h2><div className="notice">Production uses validated OIDC bearer tokens. This screen only configures synthetic local-development roles.</div><form className="panel" onSubmit={submit}><label>Roles<input name="roles" defaultValue={saved} required/></label><button>Save local roles</button></form><p>Active local roles: <b>{saved}</b></p></>;
}
