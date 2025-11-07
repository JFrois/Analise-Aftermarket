<%@ Page Language="C#" %>
<script runat="server">
    protected void Page_Load(object sender, EventArgs e)
    {
        string u = "";
        string user = "";

        // Tenta obter a identidade do usuário de várias formas
        if (Context != null && Context.User != null && Context.User.Identity != null) {
            u = Context.User.Identity.Name;
        }
        if (string.IsNullOrEmpty(u)) {
            u = Request.ServerVariables["AUTH_USER"];
        }
        if (string.IsNullOrEmpty(u)) {
            u = Request.ServerVariables["LOGON_USER"];
        }

        if (string.IsNullOrEmpty(u)) {
            // Se não autenticado, força handshake 401 (se Windows Auth estiver ativo no IIS)
            Response.StatusCode = 401;
            Response.End();
            return;
        }

        // Remove o domínio (ex: "YOUR-DOMAIN\") para passar apenas o username
        // Ajuste o regex ou string replace conforme seu domínio real se necessário
        int backslashIndex = u.IndexOf('\\');
        if (backslashIndex >= 0) {
             user = u.Substring(backslashIndex + 1);
        } else {
             user = u;
        }

        // Redireciona para a raiz passando o user na querystring
        string target = "/?user=" + Server.UrlEncode(user);
        Response.Redirect(target, true);
    }
</script>
<!DOCTYPE html>
<html>
<head><title>Autenticando...</title></head>
<body></body>
</html>