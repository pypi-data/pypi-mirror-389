import os
import numpy as np

from flask import Flask, session, render_template, request

import limpid


app = Flask(__name__)
app.secret_key = 'secret_key'


# a simple page that says hello
@app.route('/', methods = ['POST', 'GET'])
def index():
    errors = []
    results = {}
    if request.method == "POST":
        # get url that the person has entered
        try:
            material = request.form['material']
            r = requests.get(material)
        except:
            errors.append(
                "Unable to get URL. Please make sure it's valid and try again."
            )
            return render_template('index.html', errors=errors)
        if r:
            # text processing
            raw = BeautifulSoup(r.text, 'html.parser').get_text()
            nltk.data.path.append('./nltk_data/')  # set the path
            tokens = nltk.word_tokenize(raw)
            text = nltk.Text(tokens)
            # remove punctuation, count raw words
            nonPunct = re.compile('.*[A-Za-z].*')
            raw_words = [w for w in text if nonPunct.match(w)]
            raw_word_count = Counter(raw_words)
            # stop words
            no_stop_words = [w for w in raw_words if w.lower() not in stops]
            no_stop_words_count = Counter(no_stop_words)
            # save the results
            results = sorted(
                no_stop_words_count.items(),
                key=operator.itemgetter(1),
                reverse=True
            )
            try:
                result = Result(
                    url=url,
                    result_all=raw_word_count,
                    result_no_stop_words=no_stop_words_count
                )
                db.session.add(result)
                db.session.commit()
            except:
                errors.append("Unable to add item to database.")
    return render_template('index.html', errors=errors, results=results)

@app.route('/sample', methods = ['POST', 'GET'])
def sample():
    errors = []
    session['Layers'] = []
    if request.method == "POST":
        try:
            name = request.form['name']
            density = request.form['density']
            makhov_parameters = request.form['makhov']
            layer = limpid.Layer(density, makhov_parameters, name)
            session['Layers'] = [layer]
        except Exception as e:
            errors.append(e)
            return render_template('sample.html', errors=errors)
    return render_template('sample.html', errors=errors, layers=session['Layers'])

@app.route('/form')
def form():
    return render_template('form.html')

@app.route('/data/', methods = ['POST', 'GET'])
def data():
    if request.method == 'GET':
        return f"The URL /data is accessed directly. Try going to '/form' to submit form"
    if request.method == 'POST':
        form_data = request.form
        e = np.fromstring(form_data['Energy'], sep=',')
        s = np.fromstring(form_data['Lineshape'], sep=',')
        ds = np.fromstring(form_data['Lineshape Deltas'], sep=',')
        l = limpid.Layer()
        print(e, s, ds)
        return render_template('data.html', form_data=form_data)
