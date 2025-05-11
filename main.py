import streamlit as st
from azure.storage.blob import BlobServiceClient
import os
import pyodbc
import uuid
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()
blobConnectionString = os.getenv('BLOB_CONNECTION_STRING')
blobContainerName = os.getenv('BLOB_CONTAINER_NAME')
blobAccountName = os.getenv('BLOB_ACCOUNT_NAME')

sqlServer = os.getenv('SQL_SERVER')
sqlDatabase = os.getenv('SQL_DATABASE')
sqlUser = os.getenv('SQL_USER')
sqlPassword = os.getenv('SQL_PASSWORD')

st.set_page_config(page_title="Gestão de Produtos", layout="wide")

# Estilo customizado
st.markdown("""
    <style>
    .stTextInput>div>div>input { font-size: 16px; }
    .stTextArea>div>textarea { font-size: 16px; }
    .stNumberInput input { font-size: 16px; }
    .css-1v3fvcr { font-size: 18px; }
    .product-card {
        border: 1px solid #44444433;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 20px;
        background-color: #f9f9f9;
    }
    </style>
""", unsafe_allow_html=True)

# Conexão com o banco
def get_connection():
    conn_str = (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={sqlServer};DATABASE={sqlDatabase};UID={sqlUser};PWD={sqlPassword};TrustServerCertificate=yes;"
    )
    return pyodbc.connect(conn_str)

# Upload da imagem no Azure Blob Storage
def upload_blob(file):
    blob_service_client = BlobServiceClient.from_connection_string(blobConnectionString)
    container_client = blob_service_client.get_container_client(blobContainerName)
    blob_name = str(uuid.uuid4()) + "_" + file.name
    blob_client = container_client.get_blob_client(blob_name)
    blob_client.upload_blob(file.read(), overwrite=True)
    image_url = f"https://{blobAccountName}.blob.core.windows.net/{blobContainerName}/{blob_name}"
    return image_url

# Inserir produto
def insert_product(product_name, product_price, product_description, product_image):
    try:
        image_url = upload_blob(product_image)
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO tbl_produtos (nome, preco, descricao, imagem_url) VALUES (?, ?, ?, ?)",
            (product_name, product_price, product_description, image_url)
        )
        conn.commit()
        conn.close()
        st.success("✅ Produto cadastrado com sucesso!")
    except Exception as e:
        st.error(f"Erro ao salvar produto: {e}")

# Listar produtos em layout bonito
def list_products():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT nome, preco, descricao, imagem_url FROM tbl_produtos")
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            st.info("Nenhum produto cadastrado ainda.")
            return

        st.subheader("🛍️ Produtos Cadastrados")
        cols = st.columns(2)

        for i, (nome, preco, descricao, imagem_url) in enumerate(rows):
            with cols[i % 2]:
                with st.container():
                    st.markdown(f"""
                        <div class="product-card">
                            <img src="{imagem_url}" style="width: 100%; max-height: 200px; object-fit: cover; border-radius: 6px;" />
                            <h4 style="margin-top: 10px;">{nome}</h4>
                            <p><strong>Preço:</strong> R$ {preco:.2f}</p>
                            <p>{descricao}</p>
                        </div>
                    """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Erro ao listar produtos: {e}")

# Formulário de cadastro
st.title("📦 Cadastro de Produtos")

with st.form("form_cadastro"):
    product_name = st.text_input("Nome do Produto")
    product_price = st.number_input("Valor do Produto", min_value=0.0, format="%.2f")
    product_description = st.text_area("Descrição do Produto")
    product_image = st.file_uploader("Imagem do Produto", type=["jpg", "jpeg", "png"])
    submitted = st.form_submit_button("Salvar Produto")

    if submitted:
        if product_name and product_price and product_description and product_image:
            insert_product(product_name, product_price, product_description, product_image)
        else:
            st.warning("Preencha todos os campos para salvar o produto.")

# Listagem
st.markdown("---")
list_products()
