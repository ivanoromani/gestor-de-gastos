# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify, render_template, session, redirect, send_file
from flask_sqlalchemy import SQLAlchemy
import os
import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import sqlite3 

DATABASE = "expenses.db"  # Aggiungi questa riga qui!

# Configurazione Flask
app = Flask(__name__, template_folder="templates", static_folder="static")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///expenses.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = "supersecretkey"

db = SQLAlchemy(app)

# Modelli del database
class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(10), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(255), nullable=True)

# Creazione del database
with app.app_context():
    db.create_all()

translations = {
    "es": {
        "title": "Gestión de Gastos",
        "date": "Fecha",
        "amount": "Importe (€)",
        "description": "Descripción",
        "add_expense": "Añadir Gasto",
        "generate_report": "Generar Reporte PDF",
        "generate_pdf": "Descargar PDF",
        "crew": "Tripulación",
        "fuel": "Combustibles",
        "shopping": "Compras",
        "maintenance": "Varios/Mantenimiento",
        "success": "¡Gasto añadido con éxito!",
        "error": "Error al añadir gasto.",
        "error_fill_fields": "Por favor, completa todos los campos.",
        "clear_expenses": "Eliminar Todas las Gastos",  # ✅ Testo per il bottone
        "delete_expenses_success": "¡Todos los gastos han sido eliminados!"  # ✅ Messaggio di conferma
    },
    "en": {
        "title": "Expense Management",
        "date": "Date",
        "amount": "Amount (€)",
        "description": "Description",
        "add_expense": "Add Expense",
        "generate_report": "Generate PDF Report",
        "generate_pdf": "Download PDF",
        "crew": "Crew",
        "fuel": "Fuel",
        "shopping": "Shopping",
        "maintenance": "Maintenance",
        "success": "Expense added successfully!",
        "error": "Error adding expense.",
        "error_fill_fields": "Please fill in all fields.",
        "clear_expenses": "Delete All Expenses",  # ✅ Testo per il bottone
        "delete_expenses_success": "All expenses have been deleted!"  # ✅ Messaggio di conferma
    },
    "it": {
        "title": "Gestione Spese",
        "date": "Data",
        "amount": "Importo (€)",
        "description": "Descrizione",
        "add_expense": "Aggiungi Spesa",
        "generate_report": "Genera Report PDF",
        "generate_pdf": "Scarica PDF",
        "crew": "Equipaggio",
        "fuel": "Carburante",
        "shopping": "Acquisti",
        "maintenance": "Manutenzione",
        "success": "Spesa aggiunta con successo!",
        "error": "Errore nell'aggiunta della spesa.",
        "error_fill_fields": "Per favore, compila tutti i campi.",
        "clear_expenses": "Elimina Tutte le Spese",  # ✅ Testo per il bottone
        "delete_expenses_success": "Tutte le spese sono state eliminate!"  # ✅ Messaggio di conferma
    }
}


# 🔹 Imposta la lingua di default (spagnolo)
@app.route('/set_language/<lang>')
def set_language(lang):
    session['lang'] = lang
    return redirect('/')

# 🔹 Pagina principale
@app.route('/')
def home():
    lang = session.get('lang', 'es')
    return render_template('index.html', lang=lang, translations=translations[lang])

# 🔹 Aggiungi spese
@app.route('/add_expense', methods=['POST'])
def add_expense():
    data = request.json
    if not data.get('date') or not data.get('amount'):
        return jsonify({'error': 'Missing fields'}), 400

    new_expense = Expense(
        date=data['date'],
        category=data['category'],
        amount=float(data['amount']),
        description=data.get('description', '')
    )
    db.session.add(new_expense)
    db.session.commit()
    return jsonify({'message': 'Expense added successfully!'}), 201

@app.route('/generate_report', methods=['GET'])
def generate_report():
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    lang = request.args.get("lang", "es")  # Default: spagnolo

    translations = {
        "es": {"title": "Reporte de Gastos", "date": "Fecha", "category": "Categoría", "amount": "Importe (€)", "description": "Descripción", "total": "Total de gastos"},
        "en": {"title": "Expense Report", "date": "Date", "category": "Category", "amount": "Amount (€)", "description": "Description", "total": "Total expenses"},
        "it": {"title": "Resoconto Spese", "date": "Data", "category": "Categoria", "amount": "Importo (€)", "description": "Descrizione", "total": "Totale spese"},
    }

    tr = translations.get(lang, translations["es"])  # Usa la lingua selezionata o default a spagnolo

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT date, category, amount, description FROM expenses WHERE date BETWEEN ? AND ?", (start_date, end_date))
    expenses = c.fetchall()
    conn.close()

    if not expenses:
        return jsonify({"error": "No expenses found"}), 404

    total_expenses = sum(row[2] for row in expenses)  # Calcola il totale

    pdf_filename = "expense_report.pdf"
    c_pdf = canvas.Canvas(pdf_filename, pagesize=letter)
    width, height = letter

    # **Titolo**
    c_pdf.setFont("Helvetica-Bold", 16)
    c_pdf.drawCentredString(width/2, height - 50, tr["title"])

    # **Intestazione della tabella**
    c_pdf.setFont("Helvetica-Bold", 12)
    y = height - 80
    c_pdf.drawString(50, y, tr["date"])
    c_pdf.drawString(150, y, tr["category"])
    c_pdf.drawString(300, y, tr["amount"])
    c_pdf.drawString(400, y, tr["description"])
    y -= 20
    c_pdf.setFont("Helvetica", 10)

    # **Dati delle spese**
    for e in expenses:
        if y < 100:
            c_pdf.showPage()
            y = height - 50
        c_pdf.drawString(50, y, e[0])  # Data
        c_pdf.drawString(150, y, e[1])  # Categoria
        c_pdf.drawString(300, y, f"{e[2]:.2f}")  # Importo
        c_pdf.drawString(400, y, e[3])  # Descrizione
        y -= 15

    # **Totale**
    y -= 20
    c_pdf.setFont("Helvetica-Bold", 14)
    c_pdf.drawString(50, y, f"{tr['total']}: {total_expenses:.2f} €")

    c_pdf.save()
    return send_file(pdf_filename, as_attachment=True)

# 🔹 Route per eliminare tutte le spese
@app.route('/clear_expenses', methods=['POST'])
def clear_expenses():
    """Cancella tutti i dati salvati nel database."""
    try:
        with app.app_context():  # Assicura che sia nel contesto di Flask
            db.session.query(Expense).delete()  # Cancella tutti i record dal database
            db.session.commit()
        return jsonify({"message": "Todas las gastos han sido eliminadas"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


