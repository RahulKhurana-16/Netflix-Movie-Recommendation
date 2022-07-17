import pandas as pd
from flask import Flask, render_template,request
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import joblib
import imdb
import os



MoviesData= joblib.load('Movies_Datase.pkl') 
X = joblib.load('Movies_Learned_Features.pkl') 
my_ratings = np.zeros((9724,1))
my_movies=[]
my_added_movies=[]
mylistmov=MoviesData['title'].unique().tolist()

# print(my_added_movies)


def clean_data(x):
    return str.lower(x.replace(" ", ""))

def computeCost(X, y, theta):
   m=y.size
   s=np.dot(X,theta)-y
   j=(1/(2*m))*(np.dot(np.transpose(s),s))
#    print(j)
   return j

def gradientDescent(X, y, theta, alpha, num_iters):  
    m = float(y.shape[0])
    theta = theta.copy()
    for i in range(num_iters):
        theta=(theta)-(alpha/m)*(np.dot(np.transpose((np.dot(X,theta)-y)),X))
    return theta

def checkAndAdd(movie,rating):
    try:
            if isinstance(int(rating), str):
                    pass
    except ValueError:
            return (3)
    if (int(rating) <= 5 and int(rating) >= 0):
            movie = movie.lower()
            # movie=movie+' '
            if movie not in MoviesData['title'].unique().tolist():
                return(1)
            else:
                index=MoviesData[MoviesData['title']==movie].index.values[0]
                my_ratings[index] = rating
                movieid=MoviesData.loc[MoviesData['title']==movie, 'movieid']
                if movie in my_added_movies:
                        return(2)
                my_movies.append(movieid)
                my_added_movies.append(movie.upper())
                return(0)
    else:
            return(-1)
def url_clean(url):
    base, ext = os.path.splitext(url)
    i = url.count('@')
    s2 = url.split('@')[0]
    url = s2 + '@' * i + ext
    return url


def create_soup(x):
    return x['title']+ ' ' + x['director'] + ' ' + x['cast'] + ' ' +x['listed_in']+' '+ x['description']

def get_recommendations(title, cosine_sim):
    global result
    title=title.replace(' ','').lower()
    idx = indices[title]
    sim_scores = list(enumerate(cosine_sim[idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    sim_scores = sim_scores[1:11]
    movie_indices = [i[0] for i in sim_scores]
    result =  netflix_overall[['title','cast','director','description']].iloc[movie_indices]
    # result = result.to_frame()
    result = result.reset_index()
    del result['index']    
    return result
    
netflix_overall = pd.read_csv('netflix_titles.csv')
netflix_data = pd.read_csv('netflix_titles.csv')
netflix_data = netflix_data.fillna('')
movielist=netflix_data['title'].apply(clean_data).values.tolist()
moviename=netflix_data['title'].values.tolist()
# print(moviename)
new_features = ['title', 'director', 'cast', 'listed_in', 'description']
netflix_data = netflix_data[new_features]
for new_features in new_features:
    netflix_data[new_features] = netflix_data[new_features].apply(clean_data)
netflix_data['soup'] = netflix_data.apply(create_soup, axis=1)
count = CountVectorizer(stop_words='english')
count_matrix = count.fit_transform(netflix_data['soup'])
global cosine_sim2 
cosine_sim2 = cosine_similarity(count_matrix, count_matrix)
netflix_data=netflix_data.reset_index()
indices = pd.Series(netflix_data.index, index=netflix_data['title'])
#get_recommendations('PK', cosine_sim2)

def helper():
    out_arr = my_ratings[np.nonzero(my_ratings)]
    out_arr=out_arr.reshape(-1,1)
    idx = np.where(my_ratings)[0]
    X_1=[X[x] for x in idx]
    X_1=np.array(X_1)
    y=out_arr
    y=np.reshape(y, -1)
    theta = gradientDescent(X_1,y,np.zeros((100)),0.001,4000)
    p = X @ theta.T
    p=np.reshape(p, -1)
    predictedData=MoviesData.copy()
    predictedData['Pridiction']=p
    sorted_data=predictedData.sort_values(by=['Pridiction'],ascending=False)
    sorted_data=sorted_data[~sorted_data.title.isin(my_added_movies)]
    sorted_data=sorted_data[:40]
    return(sorted_data)
    
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html') 


@app.route('/register',methods=['POST','GET'])
def register():
    return render_template('register.html')


@app.route('/login')
def login():
    return render_template('login.html') 

@app.route('/home')
def browse():
    return render_template('browse.html')

@app.route('/searchpage')
def searchpage():
    return render_template('search.html', movname=moviename)

@app.route('/tvshow')
def tvshow():
    return render_template('tvshow.html')

@app.route('/movies')
def movies():
    return render_template('movies.html')

@app.route('/latest')
def latest():
    return render_template('latest.html')

@app.route('/mylist')
def mylist():
    return render_template('mylist.html',mylistmovname=mylistmov)

@app.route('/add', methods=['POST'])
def addmovie():
    val=request.form.get('moviename')
    rating=request.form.get('rating')
    # print(val)
    # print(rating)
    flag=checkAndAdd(val,rating)
    # print(flag)
    if (flag==1 or flag==2 or flag==3 or flag==-1):
        # print(my_added_movies)
        return render_template('mylist.html',mylistmovname=mylistmov)
    else:
        # print(my_added_movies)
        return render_template('mylist.html',mylistmovname=mylistmov,mlmovdata=my_added_movies)

@app.route('/predict', methods=['POST'])
def predict():
    if(len(my_added_movies)==0):
        return render_template('mylist.html',mylistmovname=mylistmov)
    data=helper()
    links=[]
    data=data[:14]
    data=data.reset_index(drop=True)
    titles=data['title'].values.tolist()
    access=imdb.IMDb()
    for movie in titles:
        name = movie
        movies= access.search_movie(name)[0]
        imgLink=movies['full-size cover url']
        links.append(imgLink)
    data['links']=links
    data['links']=data.links.map(lambda x:url_clean(x))
    data=data.values.tolist()
    return render_template('mylist1.html',data=data)

@app.route('/single')
def single():
    return render_template('single.html')

@app.route('/search',methods=['POST'])
def getvalue():
    moviename = request.form['moviename']
    if clean_data(moviename) not in movielist:
        return render_template('failure.html',searchedmovie=str.upper(moviename))
    get_recommendations(moviename,cosine_sim2)
    df=result
    # print(df.values.tolist())
    return render_template('result.html',  tables=df.values.tolist(), searchedmovie=str.upper(moviename))
    # return render_template('result.html',  tables=[df.to_html(classes='data')], titles=df.columns.values)

if __name__ == '__main__':
    app.run(debug=False)
