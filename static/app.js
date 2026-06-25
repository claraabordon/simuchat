// app.js - chat frontend
const telefono = "+5490000000000";
let session = null;

function appendMessage(text, who='bot'){
  const area = document.getElementById('chat-area');
  const div = document.createElement('div');
  div.className = 'message ' + (who==='bot' ? 'bot' : 'user');
  div.textContent = text;
  area.appendChild(div);
  area.scrollTop = area.scrollHeight;
}

async function sendMessage(text){
  appendMessage(text, 'user');
  const res = await fetch('/api/message', {
    method: 'POST', headers: {'Content-Type':'application/json'},
    body: JSON.stringify({telefono, mensaje: text})
  });
  const data = await res.json();
  session = data.datos_sesion;
  const botMsg = data.mensaje_respuesta || data.mensaje_proximo_prompt || '';
  if(botMsg) appendMessage(botMsg, 'bot');
}

window.addEventListener('DOMContentLoaded', ()=>{
  document.getElementById('send-btn').addEventListener('click', ()=>{
    const input = document.getElementById('input-msg');
    const txt = input.value.trim();
    if(!txt) return;
    sendMessage(txt);
    input.value='';
  });

  document.getElementById('input-msg').addEventListener('keydown', (e)=>{
    if(e.key==='Enter') document.getElementById('send-btn').click();
  });

  // welcome
  appendMessage('Bienvenido al formulario alternativo — escribí "hola" para comenzar.\nTambién podés ingresar tu Número de Prestador directamente. Ej: 12345');
});
