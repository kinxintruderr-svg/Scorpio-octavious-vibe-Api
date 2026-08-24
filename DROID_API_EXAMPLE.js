// Example pattern for the APK.
// Replace API_BASE with your HTTPS backend URL after deployment.
var API_BASE = "https://YOUR-BACKEND-DOMAIN.example";

function ApiPost(path, data, token, done){
    var headers = {"Content-Type":"application/json"};
    if(token) headers["Authorization"]="Bearer "+token;
    app.HttpRequest(API_BASE+path, "POST", JSON.stringify(data), headers,
        function(status, body){
            if(status>=200 && status<300) done(null, JSON.parse(body));
            else done(body || "Request failed", null);
        });
      }
