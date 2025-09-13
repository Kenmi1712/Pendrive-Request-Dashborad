from flask import Flask, request, render_template, redirect, url_for
from models import db, PendriveRequest

@app.route('/request_pendrive', methods=['POST'])
def request_pendrive():
    purpose = request.form.get('purpose')  # Get from submitted form
    ip_addr = request.remote_addr          # Get client IP
    new_req = PendriveRequest(ip_address=ip_addr, purpose=purpose)
    db.session.add(new_req)
    db.session.commit()
    return redirect(url_for('main_dashboard'))