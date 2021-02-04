from flask import Flask, render_template, request, redirect, url_for, session
from py2neo import *
from uuid import uuid4

app = Flask(__name__)
app.config['SECRET_KEY'] = 'ini rahasia'

# Graph DB Connection
graph = Graph("bolt://localhost:7687",auth=("neo4j","admin"))
# Unique Constraint

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
	if request.method == 'GET':
		return render_template('registration.html')
	else:
		name = request.form['name']
		username = request.form['username']
		password = request.form['password']
		uid = str(uuid4())

		# check if username already exists
		user = graph.run("match (n:User) where n.username='{}' return n".format(username)).data()
		if len(user) == 1:
			return redirect(url_for('registration'))
		else:
			user = graph.run("create (a:User {name:$name,username:$username,password:$password,uid:$uid})",name=name,username=username,password=password,uid=uid)
			return redirect(url_for('login'))

@app.route('/login',methods=['GET','POST'])
def login():
	if islogin():
		return redirect(url_for('home'))
	if request.method == 'GET':
		return render_template('login.html')
	else:
		username = request.form['username']
		password = request.form['password']
		# Check user if exist
		user = matching.NodeMatcher(graph).match("User",username=username,password=password).first()
		if user == None:
			return redirect(url_for('login'))
		else:
			session['login']=True
			session['user'] = user['uid']
			return redirect(url_for('home'))

@app.route('/logout')
def logout():
	session.clear()
	return redirect(url_for('index'))

@app.route('/home')
def home():
	if islogin():
		query = graph.run("match (a:User {uid:$uid})-[:IS_DOING]-> (b:Todo {is_complete:false}) return b as data ",uid=session['user'])
		data = []
		for i in query:
			d = {'is_complete':i['data']['is_complete'],'todo_name':i['data']['todo_name'],'uid':i['data']['uid']}
			data.append(d)
		return render_template('home.html',data=data)
	else:
		return redirect(url_for('login'))

@app.route('/add_todo',methods=['GET','POST'])
def add_todo():
	if islogin():
		if request.method == 'GET':
			return render_template('add_todo.html')
		else:
			todo_name = request.form['todo_name']
			uid = str(uuid4())
			is_complete = False
			insert_todo = graph.run("create (a:Todo {todo_name:$todo_name,uid:$uid,is_complete:$is_complete})",todo_name=todo_name,uid=uid,is_complete=is_complete)
			relationship = graph.run("match (a:User {uid:$uid_user}),(b:Todo {uid:$uid_todo}) merge (a)-[:IS_DOING]->(b)",uid_user=session['user'],uid_todo=uid)
			return redirect(url_for('home'))
	else:
		return redirect(url_for('login'))

@app.route('/delete_todo/<uid>')
def delete_todo(uid):
	if islogin():
		is_connect = graph.run("return exists((:User {uid:$uid_user})-[:IS_DOING]->(:Todo {uid:$uid_todo})) as connected",uid_user=session['user'],uid_todo=uid)
		if is_connect:
			delete_relation = graph.run("match (a:User {uid:$uid_user})-[r]-(b:Todo {uid:$uid_todo}) delete r",uid_user=session['user'],uid_todo=uid)
			delete_todod = graph.run("match (a:Todo {uid:$uid}) delete a ",uid=uid)
			return redirect(url_for('home'))
		else:
			return redirect(url_for('home'))
	else:
		return redirect(url_for('login'))

@app.route('/edit_todo/<uid>',methods=['GET','POST'])
def edit_todo(uid):
	if islogin():
		if request.method == 'GET':
			is_connect = graph.run("return exists((:User {uid:$uid_user})-[:IS_DOING]->(:Todo {uid:$uid_todo})) as connected",uid_user=session['user'],uid_todo=uid)
			if is_connect:
				todo = matching.NodeMatcher(graph).match("Todo",uid=uid).first()
				return render_template('edit_todo.html',data=todo)
			else:
				return redirect(url_for('home'))
		else:
			todo_name = request.form['todo_name']
			is_connect = graph.run("return exists((:User {uid:$uid_user})-[:IS_DOING]->(:Todo {uid:$uid_todo})) as connected",uid_user=session['user'],uid_todo=uid)
			if is_connect:
				edit_todo = graph.run("match (a:Todo {uid:$uid}) set a.todo_name=$todo_name ",uid=uid,todo_name=todo_name)
				return redirect(url_for('home'))
			else:
				return redirect(url_for('home'))
	else:
		return redirect(url_for('login'))

@app.route('/mark_todo/<uid>')
def mark_todo(uid):
	if islogin():
		is_connect = graph.run("return exists((:User {uid:$uid_user})-[:IS_DOING]->(:Todo {uid:$uid_todo})) as connected",uid_user=session['user'],uid_todo=uid)
		if is_connect:
			is_complete = True
			edit_todo = graph.run("match (a:Todo {uid:$uid}) set a.is_complete=$is_complete ",uid=uid,is_complete=is_complete)
			return redirect(url_for('home'))
		else:
			return redirect(url_for('home'))
	else:
		return redirect(url_for('login'))

if __name__ == "__main__":
	app.run(debug=True)
