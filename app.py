from flask import Flask, render_template, request, redirect, url_for, session
from neomodel import *
from uuid import uuid4

app = Flask(__name__)
app.config['SECRET_KEY'] = 'ini rahasia'

# database config
config.DATABASE_URL = 'bolt://neo4j:admin@localhost:7687'

# database object mapper
class Todo(StructuredNode):
	uid = StringProperty(unique_index=True, default=uuid4)
	todo_name = StringProperty()
	is_complete = BooleanProperty(default=False)
	
class User(StructuredNode):
	uid = StringProperty(unique_index=True, default=uuid4)
	name = StringProperty()
	username = StringProperty(unique_index=True)
	password = StringProperty()
	# user relasionsip to Todo Node
	todo = RelationshipTo(Todo, 'IS_DOING')

# custom function
def islogin():
	if 'login' in session:
		return True

@app.route('/')
def index():
	if islogin():
		return redirect(url_for('home'))
	return render_template('index.html')

@app.route('/registration',methods=['GET','POST'])
def registration():
	if islogin():
		return redirect(url_for('home'))
	else:
		if request.method == 'GET':
			return render_template('registration.html')
		else:
			try:
				name = request.form['name']
				username = request.form['username']
				password = request.form['password']
				user = User(name=name,username=username,password=password).save()
				return redirect(url_for('login'))
			except UniqueProperty:
				return redirect(url_for('registration'))

@app.route('/login',methods=['GET',"POST"])
def login():
	if islogin():
		return redirect(url_for('home'))
	else:
		if request.method == 'GET':
			return render_template('login.html')
		else:
			try:
				username = request.form['username']
				password = request.form['password']
				
				user = User.nodes.get(username=username,password=password)
				session['login'] = True
				session['user'] = user.uid
				return redirect(url_for('home'))
			except DoesNotExist:
				return redirect(url_for('login'))

@app.route('/logout')
def logout():
	session.clear()
	return redirect(url_for('index'))

@app.route('/home')
def home():
	if islogin():
		user = User.nodes.get(uid=session['user'])
		todo = user.todo.filter(is_complete=False)
		todo = list(todo)
		todo = todo[::-1]
		return render_template('home.html', data=todo)
	else:
		return redirect(url_for('index'))

@app.route('/add_todo',methods=['GET','POST'])
def add_todo():
	if islogin():
		if request.method == 'GET':
			return render_template('add_todo.html')
		else:
			todo = request.form['todo_name']
			todo = Todo(todo_name=todo).save()
			user = User.nodes.get(uid=session['user'])
			user.todo.connect(todo)
			return redirect(url_for('home'))
	else:
		return redirect(url_for('login'))

@app.route('/delete_todo/<uid>')
def delete_todo(uid):
	if islogin():
		try:
			user = User.nodes.get(uid=session['user'])
			todo = Todo.nodes.get(uid=uid)
			if user.todo.is_connected(todo):
				user.todo.disconnect(todo)
				todo.delete()	
			return redirect(url_for('home'))
		except DoesNotExist:
			return redirect(url_for('home'))
	else:
		return redirect(url_for('index'))

@app.route('/edit_todo/<uid>',methods=['GET','POST'])
def edit_todo(uid):
	if islogin():
		if request.method == 'GET':
			try:
				user = User.nodes.get(uid=session['user'])
				todo = Todo.nodes.get(uid=uid)
				if user.todo.is_connected(todo):
					return render_template('edit_todo.html',data=todo)
				else:
					return redirect(url_for('home'))
			except DoesNotExist:
				return redirect(url_for('home'))
		else:
			try:
				todo_name = request.form['todo_name']
				user = User.nodes.get(uid=session['user'])
				todo = Todo.nodes.get(uid=uid)
				if user.todo.is_connected(todo):
					todo.todo_name = todo_name
					todo.save()
					return redirect(url_for('home'))
				else:
					return redirect(url_for('home'))
			except DoesNotExist:
				return redirect(url_for('home'))
	else:
		return redirect(url_for('login'))

@app.route('/mark_todo/<uid>')
def mark_todo(uid):
	if islogin():
		try:
			user = User.nodes.get(uid=session['user'])
			todo = Todo.nodes.get(uid=uid)
			if user.todo.is_connected(todo):
				todo.is_complete = True
				todo.save()
				return redirect(url_for('home'))
			else:
				return redirect(url_for('home'))
		except DoesNotExist:
			return redirect(url_for('home'))
	else:
		return redirect(url_for('login'))

if __name__ == "__main__":
	app.run(debug=True)
