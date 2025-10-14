# coding: utf-8
import time
import re
import telepot
import logging
import json
import os

# 📦 Versão do bot
BOT_VERSION = "1.0.0"

# 📁 Caminho para salvar os dados
ARQUIVO_DADOS = "dados_palavras.json"

# 📜 Caminho do arquivo de segredos
ARQUIVO_SEGREDOS = ".telegram_bot_secret"

# Configuração do logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# ➕ Dicionário: {id_usuario: set(palavras)}
user_keywords = {}

# 💡 Função para ler variáveis do arquivo .telegram_bot_secret
def carregar_segredos(caminho):
    segredos = {}
    try:
        with open(caminho, encoding="utf-8") as f:
            for linha in f:
                linha = linha.strip()
                if not linha or "=" not in linha:
                    continue
                chave, valor = linha.split("=", 1)
                segredos[chave.strip()] = valor.strip()
        logging.info("🔐 Variáveis carregadas de .telegram_bot_secret")
    except Exception as e:
        logging.error(f"❌ Erro ao ler {caminho}: {e}")
    return segredos

# Carrega token e canal
segredos = carregar_segredos(ARQUIVO_SEGREDOS)
BOT_TOKEN = segredos.get("TELEGRAM_BOT_TOKEN")
CANAL_MONITORADO_ID = segredos.get("TELEGRAM_CHANNEL_ID")
CANAL_USERNAME = segredos.get("TELEGRAM_CHANNEL_USERNAME")  # deve ser o nome público do canal (ex: lamorimpromos)

if not BOT_TOKEN or not CANAL_MONITORADO_ID:
    raise SystemExit("❌ Erro: verifique se TELEGRAM_BOT_TOKEN e TELEGRAM_CHANNEL_ID estão definidos em .telegram_bot_secret")

try:
    CANAL_MONITORADO_ID = int(CANAL_MONITORADO_ID)
except:
    raise SystemExit("❌ Erro: TELEGRAM_CHANNEL_ID deve ser um número inteiro válido (ex: -1001936843102)")

# Inicializa o bot
bot = telepot.Bot(BOT_TOKEN)

# 💾 Salvar dados
def salvar_dados():
    try:
        with open(ARQUIVO_DADOS, 'w', encoding='utf-8') as f:
            json.dump({str(k): list(v) for k, v in user_keywords.items()}, f, ensure_ascii=False, indent=2)
        logging.info("💾 Dados salvos com sucesso.")
    except Exception as e:
        logging.error(f"Erro ao salvar dados: {e}")

# 📂 Carregar dados
def carregar_dados():
    global user_keywords
    if os.path.exists(ARQUIVO_DADOS):
        try:
            with open(ARQUIVO_DADOS, 'r', encoding='utf-8') as f:
                dados = json.load(f)
                user_keywords = {int(k): set(v) for k, v in dados.items()}
            logging.info("📂 Dados carregados com sucesso.")
        except Exception as e:
            logging.error(f"Erro ao carregar dados: {e}")

# 💬 Função principal para lidar com mensagens privadas (chat)
def on_chat_message(msg):
    try:
        content_type, chat_type, chat_id = telepot.glance(msg)
        text = msg.get("text", "").strip()
        if not text or chat_type != "private":
            return

        if chat_id not in user_keywords:
            user_keywords[chat_id] = set()

        # 🏁 Comandos principais
        if text == "/start":
            bot.sendMessage(
                chat_id,
                f"📢 *Bem-vindo ao Lamorim das Promoções Avisos!*\n\n"
                f"Versão atual: *{BOT_VERSION}*\n\n"
                "Aqui você pode cadastrar palavras-chave para receber alertas de ofertas.\n\n"
                "📝 `/add` — Adicionar palavra-chave\n"
                "📋 `/lista` — Ver suas palavras cadastradas\n"
                "🗑 `/apagar` — Remover uma palavra\n"
                "😱 `/apagartudo` — Remover todas as palavras\n"
                "☕ `/doar` — Ajude o projeto\n"
                "🆙 `/versao` — Mostrar a versão atual do bot\n\n"
                "Para começar, use `/add desconto` para cadastrar a palavra *desconto*.",
                parse_mode="Markdown"
            )

        elif text == "/apagartudo":
            user_keywords[chat_id].clear()
            salvar_dados()
            bot.sendMessage(chat_id, "🧹 Todas as palavras foram removidas da sua lista.")

        elif text.startswith("/add"):
            palavra = text[len("/add"):].strip().lower()
            if palavra:
                user_keywords[chat_id].add(palavra)
                salvar_dados()
                bot.sendMessage(chat_id, f"✅ Palavra adicionada: *{palavra}*", parse_mode="Markdown")
            else:
                bot.sendMessage(chat_id, "⚠️ Use `/add palavra` para adicionar uma palavra-chave.", parse_mode="Markdown")

        elif text == "/lista":
            palavras = user_keywords.get(chat_id, set())
            if palavras:
                lista = "\n".join(f"• {k}" for k in sorted(palavras))
                bot.sendMessage(chat_id, f"📋 Suas palavras cadastradas:\n{lista}")
            else:
                bot.sendMessage(chat_id, "📭 Nenhuma palavra cadastrada.")

        elif text.startswith("/apagar"):
            palavra = text[len("/apagar"):].strip().lower()
            palavras_usuario = user_keywords.get(chat_id, set())
            if not palavras_usuario:
                bot.sendMessage(chat_id, "📭 Você não tem palavras cadastradas para apagar.")
            elif not palavra:
                lista = "\n".join(f"• `/apagar {k}`" for k in sorted(palavras_usuario))
                bot.sendMessage(chat_id, f"🗑 Para apagar, use `/apagar palavra`\n\nSuas palavras:\n{lista}", parse_mode="Markdown")
            else:
                if palavra in palavras_usuario:
                    palavras_usuario.remove(palavra)
                    salvar_dados()
                    bot.sendMessage(chat_id, f"🗑 Removida: *{palavra}*", parse_mode="Markdown")
                else:
                    bot.sendMessage(chat_id, "⚠️ Palavra não encontrada.")

        elif text == "/doar":
            bot.sendMessage(chat_id, "☕ Quer apoiar o projeto?\n\n✨ *Chave PIX:* `lamorimverso@gmail.com`\n\nMuito obrigado pelo apoio! ❤️", parse_mode="Markdown")

        elif text == "/versao":
            bot.sendMessage(chat_id, f"🤖 Versão atual do bot: *{BOT_VERSION}*", parse_mode="Markdown")

    except Exception as e:
        logging.error(f"[ERRO ao processar mensagem] {e}")

# 💬 Função para lidar com postagens em canais
def on_channel_post(msg):
    try:
        chat_id = msg['chat']['id']
        message_id = msg['message_id']
        texto = (msg.get('text') or "") + " " + (msg.get('caption') or "")

        if chat_id != CANAL_MONITORADO_ID:
            return

        logging.info(f"📢 Nova mensagem no canal {chat_id}: {texto[:120]}...")

        # ✅ Link público do canal
        link_post = f"https://t.me/{CANAL_USERNAME}/{message_id}"

        for user_id, palavras in user_keywords.items():
            for palavra in palavras:
                if re.search(re.escape(palavra), texto, re.IGNORECASE):
                    try:
                        logging.info(f"✅ Palavra '{palavra}' encontrada para {user_id}, enviando aviso...")

                        # ➡️ Encaminha a mensagem original do canal primeiro
                        bot.forwardMessage(
                            user_id,
                            chat_id,
                            message_id
                        )

                        # Mensagem especial para "cupom shopee"
                        if palavra.lower() == "cupom shopee":
                            mensagem = f"📢 Encontrei uma postagem com a palavra-chave cupom shopee:\n\n{link_post}"
                        else:
                            mensagem = f"📢 Encontrei uma postagem com a palavra-chave *{palavra}:*\n\n{link_post}"

                        # Depois envia a mensagem de alerta com o link
                        bot.sendMessage(
                            user_id,
                            mensagem,
                            parse_mode="Markdown",
                            disable_web_page_preview=False
                        )

                    except Exception as e:
                        logging.error(f"Erro ao enviar mensagem para {user_id}: {e}")

    except Exception as e:
        logging.error(f"Erro no on_channel_post: {e}")

# 🏁 Loop principal
def main():
    logging.info(f"🤖 Bot inicializando... (versão {BOT_VERSION})")
    carregar_dados()
    last_update_id = None

    while True:
        try:
            updates = bot.getUpdates(offset=last_update_id, timeout=10)
            for update in updates:
                last_update_id = update['update_id'] + 1

                if 'message' in update:
                    on_chat_message(update['message'])

                if 'channel_post' in update:
                    on_channel_post(update['channel_post'])

        except Exception as e:
            logging.error(f"[ERRO no loop principal] {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
