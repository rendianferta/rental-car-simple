from flask import Flask, render_template, request, redirect, url_for, session, flash
from db_config import get_db, close_db
from datetime import datetime, timedelta


app = Flask(__name__)
app.secret_key = 'your_secret_key'

@app.teardown_appcontext
def teardown_db(exception):
    close_db(exception)


@app.route('/')
def index():
    category = request.args.get('category')  
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    if category:  
        cursor.execute('SELECT * FROM cars WHERE category = %s AND status = "available"', (category,))
    else:  
        cursor.execute('SELECT * FROM cars WHERE status = "available"')
    
    cars = cursor.fetchall()
    
    cursor.execute('SELECT DISTINCT category FROM cars')
    categories = cursor.fetchall()
    
    return render_template('index.html', cars=cars, categories=categories, selected_category=category)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        db = get_db()
        cursor = db.cursor()

        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        existing_user = cursor.fetchone()

        if existing_user:
            flash('Username already exists. Please choose another.', 'error')
            return redirect(url_for('register'))

        cursor.execute('INSERT INTO users (username, password, role) VALUES (%s, %s, "member")', (username, password))
        db.commit()
        
        flash('Registration successful. Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute('SELECT * FROM users WHERE username=%s AND password=%s', (username, password))
        user = cursor.fetchone()
        if user:
            session['user_id'] = user['id']
            session['role'] = user['role']
            return redirect(url_for('index'))
        else:
            flash('Invalid credentials!', 'error')
    return render_template('login.html')

@app.route('/rent/<int:car_id>', methods=['GET', 'POST'])
def rent(car_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if session['role'] == 'admin':
        flash('Admin is not allowed to rent cars!', 'error')
        return redirect(url_for('index'))
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    # Cek apakah mobil available
    cursor.execute('SELECT * FROM cars WHERE id=%s AND status="available"', (car_id,))
    car = cursor.fetchone()
    
    if not car:
        flash('Car is not available for rent!', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        due_date = request.form['due_date']  # Ambil dari form
        print(due_date)
        cursor = db.cursor()
        cursor.execute('INSERT INTO rentals (user_id, car_id, status, due_date) VALUES (%s, %s, "pending", %s)', (session['user_id'], car_id, due_date))
        cursor.execute('UPDATE cars SET status=%s WHERE id=%s', ("rented", car_id))
        db.commit()
        flash('Rental request submitted!', 'success')
        return redirect(url_for('index'))
    return render_template('rent_request.html', car=car)

@app.route('/return/<int:rental_id>')
def return_car(rental_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    print("Halloooo")
    db = get_db()
    cursor = db.cursor(dictionary=True)

    # Ambil detail rental yang sedang disewa oleh user
    cursor.execute('SELECT * FROM rentals WHERE id=%s AND user_id=%s AND status=%s', (rental_id, session['user_id'], "approved"))
    rental = cursor.fetchone()
    print("Nama sayaaa")
    if rental is None:
        flash('Invalid return request.', 'error')
        return redirect(url_for('history'))
    print(f" ini adalah rental--> {rental} beressss")
    print(f"rental id : {rental_id}")

    # Update status rental menjadi "returned"
    cursor.execute('UPDATE rentals SET status=%s WHERE id=%s', ("complete", rental_id))
    
    print("jalan")
    # Update status mobil menjadi "available"
    cursor.execute('UPDATE cars SET status=%s WHERE id=%s', ("available", rental['car_id']))

    db.commit()

    flash('Car returned successfully!', 'success')
    return redirect(url_for('history'))



@app.route('/admin/approvals')
def approvals():
    if session.get('role') != 'admin':
        return redirect(url_for('index'))
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute('SELECT rentals.id, users.username, cars.name, rentals.due_date FROM rentals JOIN users ON rentals.user_id=users.id JOIN cars ON rentals.car_id=cars.id WHERE rentals.status="pending"')
    requests = cursor.fetchall()
    return render_template('admin_approval.html', requests=requests)


@app.route('/admin/approve/<int:rental_id>')
def approve(rental_id):
    if session.get('role') != 'admin':
        return redirect(url_for('index'))
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('SELECT car_id FROM rentals WHERE id=%s', (rental_id,))
    car_id = cursor.fetchone()[0]
    
    cursor.execute('UPDATE rentals SET status="approved" WHERE id=%s', (rental_id,))
    
    cursor.execute('UPDATE cars SET status="rented" WHERE id=%s', (car_id,))
    db.commit()
    flash('Rental approved and car marked as rented!', 'success')
    return redirect(url_for('approvals'))

@app.route('/admin/reject/<int:rental_id>')  
def reject(rental_id):
    if session.get('role') != 'admin':
        return redirect(url_for('index'))
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('SELECT car_id FROM rentals WHERE id=%s', (rental_id,))
    car_id = cursor.fetchone()[0]
    
    cursor.execute('UPDATE rentals SET status="rejected" WHERE id=%s', (rental_id,))
    
    cursor.execute('UPDATE cars SET status="available" WHERE id=%s', (car_id,))
    db.commit()
    flash('Rental request rejected!', 'error')
    return redirect(url_for('approvals'))




@app.route('/admin/add_car', methods=['GET', 'POST'])
def add_car():
    if session.get('role') != 'admin':
        return redirect(url_for('index'))
    if request.method == 'POST':
        name = request.form['name']
        category = request.form['category']
        status = request.form['status']
        
        db = get_db()
        cursor = db.cursor()
        cursor.execute('INSERT INTO cars (name, category, status) VALUES (%s, %s, %s)', (name, category, status))
        db.commit()
        flash('Car added successfully!', 'success')
        return redirect(url_for('index'))
    return render_template('add_car.html')

@app.route('/history')
def history():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute('SELECT rentals.id, cars.name, rentals.status, rentals.due_date FROM rentals JOIN cars ON rentals.car_id=cars.id WHERE rentals.user_id=%s', (session['user_id'],))
    history = cursor.fetchall()
    return render_template('rental_history.html', history=history)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
