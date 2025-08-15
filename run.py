from flask import Flask, render_template, jsonify, request, session, redirect
import requests
import sqlite3
import yfinance as yf


app = Flask(__name__)
app.secret_key = 'chave_da_sessao'
 
nome_usuario = None

stock_symbols = [
    {"symbol": "PETR4.SA", "name": "Petrobras PN"},
    {"symbol": "VALE3.SA", "name": "Vale ON"},
    {"symbol": "ITUB4.SA", "name": "Itaú Unibanco PN"},
    {"symbol": "BBDC4.SA", "name": "Bradesco PN"},
    {"symbol": "ABEV3.SA", "name": "Ambev ON"},
    {"symbol": "BBAS3.SA", "name": "Banco do Brasil ON"},
    {"symbol": "ELET3.SA", "name": "Eletrobras ON"},
    {"symbol": "WEGE3.SA", "name": "WEG ON"}
]

# Suas chaves do Google reCAPTCHA
RECAPTCHA_SECRET_KEY = "6Ldy54UqAAAAAB-uGvvihln5Cvo9eRKA4KtMFHuf"

# Dicionário de perguntas e respostas
qa_data = {
    "O que é uma ação?": "Uma ação representa uma pequena parte de uma empresa. Ao comprar ações, você se torna sócio dessa empresa.",
    "Como funciona a bolsa de valores?": "A bolsa de valores é um mercado onde investidores compram e vendem ações e outros ativos.",
    "Qual o horário de funcionamento da bolsa?": "No Brasil, a B3 opera das 10h às 17h, com o after-market das 17h30 às 18h.",
    "O que é uma ação preferencial?": "Ações preferenciais são aquelas que dão ao investidor preferência no recebimento de dividendos, mas sem direito a voto.",
    "O que é uma ação ordinária?": "Ações ordinárias dão direito a voto nas assembleias da empresa e participação nos lucros.",
    "Como posso investir em ações?": "Você pode investir em ações através de uma corretora de valores, comprando e vendendo ações na bolsa de valores.",
    "O que é a B3?": "A B3 é a bolsa de valores oficial do Brasil, onde ações, commodities e outros ativos são negociados.",
    "O que são dividendos?": "Dividendos são uma parte do lucro da empresa distribuída aos acionistas.",
    "Qual a diferença entre ações e ETFs?": "Ações representam uma parte de uma empresa, enquanto ETFs são fundos que possuem ações de várias empresas.",
    "O que são commodities?": "Comodities são produtos básicos, como ouro, petróleo ou grãos, negociados nas bolsas de valores."
}

@app.route("/")
def index():

    return render_template("index.html")


def get_stock_data():
    stocks_data = []
    for stock in stock_symbols:
        symbol = stock["symbol"]
        stock_obj = yf.Ticker(symbol)
        data = stock_obj.history(period="1d")
        if not data.empty:
            price = round(data['Close'].iloc[-1], 2)
            change = round(data['Close'].iloc[-1] - data['Open'].iloc[-1], 2)
            percentage_change = round(((data['Close'].iloc[-1] - data['Open'].iloc[-1]) / data['Open'].iloc[-1]) * 100, 2)

            stocks_data.append({
                "name": stock["name"],
                "symbol": symbol,
                "price": price,
                "change": change,
                "percentage_change": percentage_change
            })
    return stocks_data

@app.route("/bolsa")
def bolsa():
    nome = session.get('nome_usuario')  # Obtém o nome diretamente da sessão
    if nome is None:  # Verifica se o nome do usuário está na sessão
        return redirect('/')
 
    stocks = get_stock_data()
    return render_template("bolsa.html", stocks=stocks, nome=nome)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
 
        nome = request.form['nome']
        senha = request.form['senha']
        token = request.form.get("g-recaptcha-response")
 
        conexao = sqlite3.connect('models/site_financeiro.db')
        cursor = conexao.cursor()
 
        sql = "SELECT * from tb_login WHERE nome=? AND senha=?"
        cursor.execute(sql, (nome, senha))
 
        response = requests.post(
            "https://www.google.com/recaptcha/api/siteverify",
            data={
                "secret": RECAPTCHA_SECRET_KEY,
                "response": token,
            },
        ).json()
 
        login_usuario = cursor.fetchone()
        if not login_usuario:  
            return render_template('login.html', erro = "Nenhuma conta foi registrada com esses dados")  
        if not token:
            return render_template('login.html', erro = "Por favor resolva o CAPTCHA")
        else:
            session['nome_usuario'] = nome
            print(session['nome_usuario'])
            return redirect('/bolsa')
       
    return render_template("login.html")


@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if request.method == "POST":
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        senha_confirmada = request.form['senha_confirmada']
 
        session['nome_usuario'] = nome
        print(session['nome_usuario'])
 
        conexao = sqlite3.connect('models/site_financeiro.db')
        cursor = conexao.cursor()
 
        cursor.execute('SELECT email FROM tb_login WHERE email = ?', (email,))
        usuario_existente = cursor.fetchone()
       
        if usuario_existente:
                conexao.close()
                return render_template('cadastro.html', erro="Este email já está em uso!")
       
        if senha != senha_confirmada:
            conexao.close()
            return render_template('cadastro.html', erro="As senhas não coincidem")
 
        with sqlite3.connect('models/site_financeiro.db') as conexao:
                cursor = conexao.cursor()
 
        sql = 'INSERT INTO tb_login (nome, email, senha) VALUES (?, ?, ?)'
        cursor.execute(sql, (nome, email, senha))
 
        conexao.commit()
        conexao.close()
 
        return redirect ('/bolsa')
   
    return render_template('cadastro.html')

def calcular_rendimento(taxa_anual, inicial, aporte_mensal, meses):
    """
    Calcula o rendimento com base em juros compostos.
    :param taxa_anual: Taxa de juros anual (em %)
    :param inicial: Valor inicial investido
    :param aporte_mensal: Valor mensal aplicado
    :param meses: Número de meses
    :return: Saldo final
    """
    taxa_mensal = (taxa_anual / 100) / 12
    saldo = inicial
    for _ in range(meses):
        saldo = saldo * (1 + taxa_mensal) + aporte_mensal
    return round(saldo, 2)

@app.route("/investir", methods=["GET", "POST"])
def investir():
    nome = session.get('nome_usuario')  # Obtém o nome diretamente da sessão
    if nome is None:  # Verifica se o nome do usuário está na sessão
        return redirect('/')
    
    resultados = []
    if request.method == 'POST':
        # Receber dados do formulário
        inicial = float(request.form.get('inicial', 0))
        aporte = float(request.form.get('aporte', 0))
        meses = int(request.form.get('meses', 0))

        # Taxas de diferentes tipos de investimentos
        taxas = {
            'CDB': 12.15,
            'LCI/LCA': 9.48,
            'Tesouro Prefixado': 10.50,
            'Tesouro Selic': 11.15,
            'Tesouro IPCA+': 6.50,
            'Poupança': 6.17
        }

        # Calcular rendimentos para cada tipo
        for investimento, taxa in taxas.items():
            rendimento = calcular_rendimento(taxa, inicial, aporte, meses)
            resultados.append({'tipo': investimento, 'rendimento': rendimento})

        # Ordenar por maior rendimento
        resultados = sorted(resultados, key=lambda x: x['rendimento'], reverse=True)

    #Parte do formulario das perguntas
    question = None
    answer = None
    
    if request.method == 'POST':
        if 'question' in request.form:
            question = request.form['question']
            answer = qa_data.get(question, "Desculpe, não tenho uma resposta para essa pergunta.")
        else:
            question = None
            answer = "Escolha uma pergunta para começar."

    return render_template('investimento.html', resultados=resultados,  question=question, answer=answer, nome=nome, questions=qa_data.keys())


@app.route('/api/coins')
def get_coins():
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": 10,
        "page": 1
    }

    # Fazendo a requisição para a API
    response = requests.get(url, params=params)
    data = response.json()

    # Retornando os dados em formato JSON
    return jsonify(data)

@app.route("/acionista")
def acionistas():
 
    nome = session.get('nome_usuario')
    if nome is None:
        return redirect ('/')
 
    return render_template("acionistas.html", nome=nome)
 
@app.route('/logout')
def logout():
     
    session.clear()
 
    return redirect('/')

if __name__ == "__main__":
    app.run(debug=True)
