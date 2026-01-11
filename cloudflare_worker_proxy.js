export default {
  async fetch(request, env) {
    // Sadece POST isteklerine izin ver
    if (request.method !== "POST") {
      return new Response("Method not allowed", { status: 405 });
    }

    const url = "https://smsapi.nac.com.tr/v1/json/syncreply/Submit";
    
    // Gelen isteğin body'sini al
    const body = await request.text();
    
    // NAC API'ye isteği ilet
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: body
    });

    // NAC API'den gelen cevabı geri döndür
    const responseBody = await response.text();
    return new Response(responseBody, {
      status: response.status,
      headers: {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*" // CORS için
      }
    });
  }
};