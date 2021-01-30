from flask import Flask, request, jsonify, render_template, redirect, session, url_for, g
import time
import os
import shutil
import json
import networkx as nx
# import matplotlib.pyplot as plt
import collections
import seaborn as sns
import requests
from datetime import datetime

from bokeh.io import output_file, show
from bokeh.models import HoverTool, ColumnDataSource, LinearColorMapper, BoxSelectTool, Circle,  MultiLine, NodesAndLinkedEdges, Plot, Range1d, TapTool, BoxZoomTool, ResetTool, WheelZoomTool, PanTool
from bokeh.palettes import Spectral4
from bokeh.plotting import from_networkx, figure
from bokeh.embed import components

from bokeh.transform import linear_cmap

from bot import Bot
from secrets import username_, password_, consumer_key_, consumer_secret_, access_token_, access_token_secret_

import tweepy
from bluebird import BlueBird
import random


# Init User
class User:
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

    def __repr__(self):
        return f'<User: {self.username}>'

users = []
users.append(User(id=1, username='user', password='satu'))
users.append(User(id=2, username='admin', password='zero'))
users.append(User(id=3, username='Carlos', password='somethingsimple'))

# Init App
app = Flask(__name__)
app.secret_key = 'secretkeysatu'

# Init directory & time
BASEDIR = os.path.abspath(os.path.dirname(__file__))
DATE_NOW = datetime.now()

# Init tweepy
consumer_key = consumer_key_
consumer_secret = consumer_secret_
access_token = access_token_
access_token_secret = access_token_secret_

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth,wait_on_rate_limit=True)

def generate_txt(relations_file, my_followers_arr, username):
    relations = open(relations_file, 'w+')
    for key in my_followers_arr:
        line = key + " " + "https://www.instagram.com/" + username + "/\n" + "https://www.instagram.com/" + username + "/ " + key + "\n"
        relations.write(line)


def get_start_profile(dir_riwayat):
    with open(dir_riwayat+'/start_profile.txt') as f:
        return int(f.readline())


def get_my_followers_from_txt(dir_riwayat):
    my_followers_arr = []
    with open(dir_riwayat+'/profil.json') as f:
        data = json.load(f)
        for line in data:
            my_followers_arr.append("https://www.instagram.com/"+line['profil_name']+"/")
    print("- Profil Tanpa Duplikat",len(list(dict.fromkeys(my_followers_arr))))
    return list(dict.fromkeys(my_followers_arr)) # return list tanpa duplikat

def sort_and_small_dict(d, n): # fungsi mengurutkan
    sorted_dict = collections.OrderedDict(sorted(d.items(), key=lambda x: -x[1]))
    firstnpairs = list(sorted_dict.items())[:n]
    return firstnpairs

def centrality_to_str_arr(centrality, dir_relation): 
    str_arr = []
    G = nx.Graph()
    relations = []

    with open(dir_relation) as openfile:
        relations = json.load(openfile)
    
    for edge in relations:
        G.add_edge(edge['node1'], edge['node2'])

    for item in centrality:
        # str_arr.append(item[0] + '_' + str(nx.degree(G, item[0])) + '_' + str(round(item[1], 5)))
        str_arr.append(item[0] + ' <br>Freq: <strong>' + str(nx.degree(G, item[0])) + '</strong> <br>Cent: <strong>' + str(round(item[1], 5)) + '</strong>') # output : earth | Frekuensi (30) | 0.08 (revisi:.5) 
    return str_arr

@app.before_request
def before_request():
    g.user = None

    if 'user_id' in session:
        user = [x for x in users if x.id == session['user_id']][0]
        g.user = user

# route login
@app.route('/', methods=['POST', 'GET']) # Login Masih Error (Cek Lagi)
def index():
    if request.method == 'POST':
        session.pop('user_id', None)

        username = request.form['nama']
        password = request.form['sandi']

        if username == "":
            return redirect(url_for('index'))
        
        user = [x for x in users if x.username == username][0]
        if user and user.password == password:
            session['user_id'] = user.id
            return redirect(url_for('cari'))

        return redirect(url_for('index'))

    return render_template('login.html')

# route logout
@app.route('/logout')
def logout():
    session.pop('user_id')
    return redirect(url_for('index'))

# route Index
@app.route('/cari', methods=['POST', 'GET'])
def cari():
    if not g.user:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        riwayat = request.form['hashtag']
        # return jsonify(riwayat)
        # update = request.form['update']
        # jika request = hashtag, tampilkan data lama atau membuat data
        # jika request = update, update data
        if len(riwayat) != 0:
            hour = DATE_NOW.hour
            minute = DATE_NOW.minute
            day = DATE_NOW.day
            month = DATE_NOW.month
            year = DATE_NOW.year
            start_time = time.time()
            dir_riwayat = os.path.join(BASEDIR, "data/"+str(round(start_time, 0))+"_"+riwayat+"_"+str(hour)+"."+str(minute)+" WIB, "+str(day)+"_"+str(month)+"_"+str(year))
            
            hitung_dir = 0 # hitung jumlah direktori berdasarkan hashtag
            dir_data = os.path.join(BASEDIR, "data")
            for x in os.listdir(dir_data):
                if riwayat in x: # jika data belum tersedia, maka grab postingan, caption, hashtag dan relation
                    # jika ada tapi folder kosong belum dibuat if nya -------------------------------------------
                    dir_riwayat_cek = os.path.join(dir_data, x)
                    # hitung_dir =+ 1
                    # print(x, hitung_dir)
                    if os.listdir(dir_riwayat_cek) != []:
                        hitung_dir =+ 1
                        print(x, hitung_dir)
                        dir_riwayat = dir_riwayat_cek
                    else:
                        os.rmdir(dir_riwayat_cek) # hapus folder jika kosong
                        # return jsonify(dir_riwayat_cek+" tidak ada file")
            if hitung_dir == 0: # jika data belum tersedia, maka grab postingan, caption, hashtag dan relation
                # remove old folder
                # dir_data = os.path.join(BASEDIR, "data")
                # for x in os.listdir(dir_data):
                #     if riwayat in x:
                #         shutil.rmtree(os.path.join(dir_data, x))
                #         print(riwayat,"dihapus")
                os.mkdir(dir_riwayat) # create dir riwayat
                print(dir_riwayat)
                # Grab Posts
                arr = []

                # debug
                # return jsonify(dir_riwayat)
                
                # Grap Posts
                end_cursor = '' # penanda halaman
                tag = riwayat # tag yg mau dicari
                page_count = 1 # jumlah halaman (1 halaman kurang lebih 60 posts)

                try:
                    for i in range(0, page_count):
                        url = "https://www.instagram.com/explore/tags/{0}/?__a=1&max_id={1}".format(tag, end_cursor)
                        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36"}
                        r = requests.get(url, headers=headers)
                        data = json.loads(r.text)
                        
                        end_cursor = data['graphql']['hashtag']['edge_hashtag_to_media']['page_info']['end_cursor'] # value for the next page
                        edges = data['graphql']['hashtag']['edge_hashtag_to_media']['edges'] # list with posts
                        
                        for item in edges:
                            arr.append(item['node'])
                            print(item['node'])

                        time.sleep(2) # insurence to not reach a time limit
                except:
                    return jsonify("Error - Grap Posts")
                    
                print("End cursor:",end_cursor) # save this to restart parsing with the next page

                with open(dir_riwayat+'/posts.json', 'w') as outfile:
                    json.dump(arr, outfile) # save to json
                
                # Grab Username
                profil = []
                print('Grap Profil')
                # user_name = open(dir_riwayat+"/user_following.txt", "a+")
                for item in arr:
                    shortcode = item['shortcode']
                    print(f"[shortcode] {shortcode}")
                    url = "https://www.instagram.com/p/{0}/?__a=1".format(shortcode)
                    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36"}
                    r = requests.get(url, headers=headers)

                    try:
                        data = json.loads(r.text)
                        try:
                            profil_name = data['graphql']['shortcode_media']['owner']['username'] # get profil_name for a post
                        except:
                            profil_name = '' # if profil_name is NULL
                            print("[EXCEPT] Nama profil kosong")
                        profil.append({
                            'shortcode': shortcode, 
                            'profil_name': profil_name # hapus username yg sama
                        })
                        # save profil name to txt
                        # user_name.write("https://www.instagram.com/"+profil_name + "/\n")
                        print(profil_name)
                    except:
                        profil_name = ''
                        print("[EXCEPT] Cek")
                        # print(len(caption))
                    time.sleep(2) # just worry time out
                print("[INFO] Simpan profil.json")
                with open(dir_riwayat+'/profil.json', 'w', encoding='utf-8') as outfile:
                    json.dump(profil, outfile, ensure_ascii=False) # save to json
                
                waktu = (time.time() - start_time) # Hitung waktu proses
                print(f"Info - Data Tersedia {len(profil)} profil - {waktu:.2f} s")
                
                # return jsonify(f"Info - Data Tersedia {len(profil)} profil - {waktu:.2f} s")
            
            if not os.path.isfile(dir_riwayat+'/relations.txt'): # cek relations exist 
                # Grab Following by Bot & make relations

                relations_file = dir_riwayat+'/relations.txt'
                b = Bot()

                b.setUp()
                b.go_to_page("https://www.instagram.com/accounts/login/")
                b.login(username_, password_)

                my_followers_arr = get_my_followers_from_txt(dir_riwayat)
                
                # if not os.path.isfile(relations_file):
                #     generate_txt(relations_file, my_followers_arr, username_)

                if os.path.isfile(dir_riwayat+'/start_profile.txt'):
                    start_profile = get_start_profile(dir_riwayat)
                    print("Start scraping at profile nr " + str(start_profile))
                else:
                    start_profile = 1
                    with open(dir_riwayat+'/start_profile.txt', 'w+') as outfile:
                        outfile.write("1")

                b.get_followers(my_followers_arr, start_profile, dir_riwayat)

                waktu = (time.time() - start_time) # Hitung waktu proses
                print(f"Info IG - Data Tersedia {len(profil)} profil - {waktu:.2f} s")

                return jsonify(f"Info - Data Tersedia {len(profil)} profil - {waktu:.2f} s")

            # get data twitter
            if not os.path.isfile(dir_riwayat+'/relations_tweet.json'): # cek relations tweet exist 
                teks = []
                tw_user_id = []
                relations = []

                bulan = ['05', '10']
                tahun = [ '2020']
                # return jsonify(riwayat)

                for xi, xj in enumerate(tahun):
                    for yi, yj in enumerate(bulan):
                        if yi == 0:
                            print(bulan[yi],tahun[xi],bulan[yi+1],tahun[xi])
                            query = {
                                'fields': [
                                    {'items': [riwayat]} # hashtag yg dicari
                                ],
                                'lang': 'id',
                                'since': tahun[xi]+'-'+bulan[yi]+'-01',
                                'until': tahun[xi]+'-'+bulan[yi+1]+'-01',
                            }

                            for tweet in BlueBird().search(query):
                                print(tweet)
                                teks.append({
                                    "created_at" : tweet['created_at'],
                                    "user_id" : tweet['user_id_str'],
                                    "text" : tweet['full_text']
                                })
                                tw_user_id.append(tweet['user_id_str'])
                        # else:
                        #     if xi+1 < len(tahun):
                        #         print(bulan[yi],tahun[xi],bulan[yi-1],tahun[xi+1])
                        #         query = {
                        #             'fields': [
                        #                 {'items': [riwayat]} # hashtag yg dicari
                        #             ],
                        #             'lang': 'id',
                        #             'since': tahun[xi]+'-'+bulan[yi]+'-01',
                        #             'until': tahun[xi+1]+'-'+bulan[yi-1]+'-01',
                        #         }

                        #         for tweet in BlueBird().search(query):
                        #             print(tweet)
                        #             teks.append({
                        #                 "created_at" : tweet['created_at'],
                        #                 "user_id" : tweet['user_id_str'],
                        #                 "text" : tweet['full_text']
                        #             })
                        #             tw_user_id.append(tweet['user_id_str'])
                        time.sleep(1.5)

                print(len(teks),"tweets")

                print("Profil id:",len(tw_user_id))

                tw_user_id = list(dict.fromkeys(tw_user_id))

                print("Tanpa Duplikat:",len(tw_user_id))

                with open(dir_riwayat+'/tweet_tag.json', 'w') as outfile:
                    json.dump(teks, outfile)
                    print("Tweets Berhasil disimpan")
                    
                with open(dir_riwayat+'/tw_profil.json', 'w') as tw_outfile:
                    json.dump(tw_user_id, tw_outfile)
                    print("Profil Tweets berhasil disimpan")

                for idx_usr, usr in enumerate(tw_user_id):
                    for jdx_usr, jusr in enumerate(tw_user_id):
                        if idx_usr != jdx_usr:
                            # mencari relasi setiap akun
                            # print(tw_user_id[idx_usr],tw_user_id[jdx_usr])
                            # print(idx_usr, jdx_usr)
                            relasi = api.show_friendship(source_id = tw_user_id[idx_usr], target_id = tw_user_id[jdx_usr])
                            if relasi[0].followed_by == True:
                                print(relasi[0].screen_name, relasi[1].screen_name)
                                relations.append({
                                    "node1" : relasi[0].screen_name,
                                    "node2" : relasi[1].screen_name,
                                })
                            time.sleep(random.randint(23, 45) / 10.0)
                    ts = random.randint(73, 95) / 10.0
                    print("sleep",ts,"s")
                    time.sleep(ts)

                with open(dir_riwayat+'/relations_tweet.json', 'w') as rel_outfile:
                    json.dump(relations, rel_outfile)
                    print("Berhasil simpan relasi tweet")
            
            # konversi relation.txt to .json
            rel_ig_json = []
            with open(dir_riwayat+'/relations.txt', 'r') as openfile:
                for x in openfile:
                    rel = x.split(" ")
                    rel_ig_json.append({
                        "node1" : (rel[0][:-1]).replace("https://www.instagram.com/",""),
                        "node2" : (rel[1][:-2]).replace("https://www.instagram.com/","")
                    })

            with open(dir_riwayat+'/relations.json', 'w') as outfile:
                json.dump(rel_ig_json, outfile)

            dir_relation = os.path.join(dir_riwayat, "relations.json")
            dir_relation_tw = os.path.join(dir_riwayat, "relations_tweet.json")

            tag_html = []
            bet_cen = []
            # bet_cen_html = []
            deg_cen = []
            # deg_cen_html = []
            clo_cen = []
            # clo_cen_html = []
            eig_cen = []
            # eig_cen_html = []

            tag_html_tw = []
            bet_cen_tw = []
            # bet_cen_html = []
            deg_cen_tw = []
            # deg_cen_html = []
            clo_cen_tw = []
            # clo_cen_html = []
            eig_cen_tw = []
            # eig_cen_html = []

            G_count = nx.Graph()
            relations_c = []

            # cek jumlah nodes dan edges instagram
            with open(dir_relation) as openfile:
                relations_c = json.load(openfile)
            
            for edge in relations_c:
                G_count.add_edge(edge['node1'], edge['node2'])

            n_nodes = len(G_count)
            n_edges = G_count.number_of_edges()

            G_count_tw = nx.Graph()
            relations_c_tw = []
            # cek jumlah nodes dan edges twitter
            with open(dir_relation_tw) as openfile:
                relations_c_tw = json.load(openfile)
            
            for edge in relations_c_tw:
                G_count_tw.add_edge(edge['node1'], edge['node2'])

            n_nodes_tw = len(G_count_tw)
            n_edges_tw = G_count_tw.number_of_edges()

            # Visual Graph of Tag Instagram
            if not os.path.exists(dir_riwayat+"/tag_html.json") :
                
                print(dir_riwayat,'tidak tersedia (instagram)')
                G_symmetric = nx.Graph()
                G_temp = nx.Graph() # temporary graph utk mengurangi node yg kurang dari 100
                relations = []

                with open(dir_relation) as openfile:
                    relations = json.load(openfile)
                
                for edge in relations:
                    G_symmetric.add_edge(edge['node1'], edge['node2'])
                    G_temp.add_edge(edge['node1'], edge['node2'])

                # for i in G_temp.degree():
                #     if i[1] < 100:
                #         G_symmetric.remove_node(i[0])
                
                # set attr size and color
                node_size = {k:v*3 for k, v in G_symmetric.degree()}
                node_color = {k:v*1 for k, v in G_symmetric.degree()}

                # Set node attribute
                nx.set_node_attributes(G_symmetric, node_color, 'node_color')
                nx.set_node_attributes(G_symmetric, node_size, 'node_size')

                # Map cubehelix_palette (Untuk Warna)
                palette = sns.cubehelix_palette(21)
                pal_hex_lst = palette.as_hex()

                mapper = LinearColorMapper(palette=pal_hex_lst, low=0, high=21)

                # Init Plot
                plot = Plot(x_range=Range1d(-1.1,1.1), y_range=Range1d(-1.1,1.1))
                plot.title.text = "Graph Relations Hashtag"

                plot.add_tools(HoverTool(tooltips=[("index", "@index")]), TapTool(), BoxSelectTool(), ResetTool(), BoxZoomTool(), WheelZoomTool(), PanTool())

                # Graph render
                graph = from_networkx(G_symmetric, nx.spring_layout, scale=1, center=(0,0))

                graph.node_renderer.glyph = Circle(size='node_size', fill_color={'field': 'node_color', 'transform': mapper})
                # graph.node_renderer.glyph = Circle(size='node_size', fill_color=linear_cmap('name', 'Spectral8', min(G_symmetric.nodes()), max(G_symmetric.nodes()))
                # )

                graph.edge_renderer.glyph = MultiLine(line_color="#CCCCCC", line_alpha=0.8, line_width=1)
                graph.edge_renderer.selection_glyph = MultiLine(line_color=Spectral4[2], line_width=1)
                graph.edge_renderer.hover_glyph = MultiLine(line_color=Spectral4[1], line_width=1)

                graph.selection_policy = NodesAndLinkedEdges()

                plot.renderers.append(graph)

                # Save and get div and script
                script, div = components(plot) 
                tag_html.append({
                    'div' : div,
                    'script' : script
                })
                with open(dir_riwayat+'/tag_html.json', 'w') as outfile:
                    json.dump(tag_html, outfile) # save html part Graph
                
            else:
                with open(dir_riwayat+'/tag_html.json') as openfile:
                    tag_html = json.load(openfile)
            
            # Visual Graph of Tag Twitter
            if not os.path.exists(dir_riwayat+"/tag_html_tw.json") :
                
                print(dir_riwayat,'tidak tersedia (twitter) ')
                G_symmetric = nx.Graph()
                G_temp = nx.Graph() # temporary graph utk mengurangi node yg kurang dari 100
                relations = []

                with open(dir_relation_tw) as openfile:
                    relations = json.load(openfile)
                
                for edge in relations:
                    G_symmetric.add_edge(edge['node1'], edge['node2'])
                    G_temp.add_edge(edge['node1'], edge['node2'])

                # for i in G_temp.degree():
                #     if i[1] < 100:
                #         G_symmetric.remove_node(i[0])
                
                # set attr size and color
                node_size = {k:v*3 for k, v in G_symmetric.degree()}
                node_color = {k:v*1 for k, v in G_symmetric.degree()}

                # Set node attribute
                nx.set_node_attributes(G_symmetric, node_color, 'node_color')
                nx.set_node_attributes(G_symmetric, node_size, 'node_size')

                # Map cubehelix_palette (Untuk Warna)
                palette = sns.cubehelix_palette(21)
                pal_hex_lst = palette.as_hex()

                mapper = LinearColorMapper(palette=pal_hex_lst, low=0, high=21)

                # Init Plot
                plot = Plot(x_range=Range1d(-1.1,1.1), y_range=Range1d(-1.1,1.1))
                plot.title.text = "Graph Relations Hashtag"

                plot.add_tools(HoverTool(tooltips=[("index", "@index")]), TapTool(), BoxSelectTool(), ResetTool(), BoxZoomTool(), WheelZoomTool(), PanTool())

                # Graph render
                graph = from_networkx(G_symmetric, nx.spring_layout, scale=1, center=(0,0))

                graph.node_renderer.glyph = Circle(size='node_size', fill_color={'field': 'node_color', 'transform': mapper})

                graph.edge_renderer.glyph = MultiLine(line_color="#CCCCCC", line_alpha=0.8, line_width=1)
                graph.edge_renderer.selection_glyph = MultiLine(line_color=Spectral4[2], line_width=1)
                graph.edge_renderer.hover_glyph = MultiLine(line_color=Spectral4[1], line_width=1)

                graph.selection_policy = NodesAndLinkedEdges()

                plot.renderers.append(graph)

                # Save and get div and script
                script, div = components(plot) 
                tag_html_tw.append({
                    'div' : div,
                    'script' : script
                })
                with open(dir_riwayat+'/tag_html_tw.json', 'w') as outfile:
                    json.dump(tag_html_tw, outfile) # save html part Graph
                
            else:
                with open(dir_riwayat+'/tag_html_tw.json') as openfile:
                    tag_html_tw = json.load(openfile)


            # Betweenness centrality
            if not os.path.exists(dir_riwayat+"/bet_cen.json"):
                G_symmetric = nx.Graph()
                relations = []

                with open(dir_relation) as openfile: # open file relations.json
                    relations = json.load(openfile)

                for edge in relations:
                    G_symmetric.add_edge(edge['node1'], edge['node2'])

                bet_cen = nx.betweenness_centrality(G_symmetric)

                # # Set node size and color
                # node_size = {k:100*v for k, v in bet_cen.items()}
                # node_color = {k:15*v for k, v in bet_cen.items()}

                # # bet_cen_sort = sort_and_small_dict(bet_cen, 5)
                # for i in bet_cen.items():
                #     if i[1] < 0.01: # menghapus node yg skornya kurang dari 0.1
                #         G_symmetric.remove_node(i[0])

                # # Set node attribute
                # nx.set_node_attributes(G_symmetric, node_color, 'node_color')
                # nx.set_node_attributes(G_symmetric, node_size, 'node_size')

                # # Map cubehelix_palette (Untuk Warna)
                # palette = sns.cubehelix_palette(21)
                # pal_hex_lst = palette.as_hex()

                # mapper = LinearColorMapper(palette=pal_hex_lst, low=0, high=21)

                # # Init Plot
                # plot = Plot(x_range=Range1d(-1.1,1.1), y_range=Range1d(-1.1,1.1))
                # plot.title.text = "Graph Betweenness Centrality"

                # plot.add_tools(HoverTool(tooltips=[("index", "@index")]), TapTool(), BoxSelectTool(), ResetTool(), BoxZoomTool(), WheelZoomTool(), PanTool())

                # # Graph render
                # graph = from_networkx(G_symmetric, nx.spring_layout, scale=1, center=(0,0))

                # graph.node_renderer.glyph = Circle(size='node_size', fill_color={'field': 'node_color', 'transform': mapper})

                # graph.edge_renderer.glyph = MultiLine(line_color="#CCCCCC", line_alpha=0.8, line_width=1)
                # graph.edge_renderer.selection_glyph = MultiLine(line_color=Spectral4[2], line_width=1)
                # graph.edge_renderer.hover_glyph = MultiLine(line_color=Spectral4[1], line_width=1)

                # graph.selection_policy = NodesAndLinkedEdges()

                # plot.renderers.append(graph)

                # # Save and get div and script
                # script, div = components(plot) 
                # bet_cen_html.append({
                #     'div' : div,
                #     'script' : script
                # })
                # with open(dir_riwayat+'/bet_cen_html.json', 'w') as outfile:
                #     json.dump(bet_cen_html, outfile) # save html part Graph
                
                bet_cen = sort_and_small_dict(bet_cen, 100) # filter 100 terbesar
                with open(dir_riwayat+"/bet_cen.json", 'w') as outfile:
                    json.dump(bet_cen, outfile) # Save Bet Cen tabel
                bet_cen = centrality_to_str_arr(bet_cen, dir_riwayat+"/relations.json")
            else:
                # with open(dir_riwayat+"/bet_cen_html.json") as openfile:
                #     bet_cen_html = json.load(openfile) # load data json Graph
                with open(dir_riwayat+"/bet_cen.json") as openfile:
                    bet_cen = json.load(openfile) # load data json Tabel
                bet_cen = centrality_to_str_arr(bet_cen, dir_riwayat+"/relations.json")
            
            # Betweenness centrality Twitter
            if not os.path.exists(dir_riwayat+"/bet_cen_tw.json"):
                G_symmetric = nx.Graph()
                relations = []

                with open(dir_relation_tw) as openfile: # open file relations.json
                    relations = json.load(openfile)

                for edge in relations:
                    G_symmetric.add_edge(edge['node1'], edge['node2'])

                bet_cen_tw = nx.betweenness_centrality(G_symmetric)
                
                bet_cen_tw = sort_and_small_dict(bet_cen_tw, 100) # filter 100 terbesar
                with open(dir_riwayat+"/bet_cen_tw.json", 'w') as outfile:
                    json.dump(bet_cen_tw, outfile) # Save Bet Cen tabel
                bet_cen_tw = centrality_to_str_arr(bet_cen_tw, dir_riwayat+"/relations_tweet.json")
            else:
                # with open(dir_riwayat+"/bet_cen_html.json") as openfile:
                #     bet_cen_html = json.load(openfile) # load data json Graph
                with open(dir_riwayat+"/bet_cen_tw.json") as openfile:
                    bet_cen_tw = json.load(openfile) # load data json Tabel
                bet_cen_tw = centrality_to_str_arr(bet_cen_tw, dir_riwayat+"/relations_tweet.json")

            # Degree centrality
            if not os.path.exists(dir_riwayat+"/deg_cen.json") :
                G_symmetric = nx.Graph()
                relations = []

                with open(dir_relation) as openfile: # open file relations.json
                    relations = json.load(openfile)

                for edge in relations:
                    G_symmetric.add_edge(edge['node1'], edge['node2'])

                deg_cen = nx.degree_centrality(G_symmetric)

                # Membuat graph 
                # # Set node size and color
                # node_size = {k:100*v for k, v in deg_cen.items()}
                # node_color = {k:15*v for k, v in deg_cen.items()}

                # for i in deg_cen.items():
                #     if i[1] < 0.1: # menghapus node yg skornya kurang dari 0.1
                #         G_symmetric.remove_node(i[0])

                # # Set node attribute
                # nx.set_node_attributes(G_symmetric, node_color, 'node_color')
                # nx.set_node_attributes(G_symmetric, node_size, 'node_size')

                # # Map cubehelix_palette (Untuk Warna)
                # palette = sns.cubehelix_palette(21)
                # pal_hex_lst = palette.as_hex()

                # mapper = LinearColorMapper(palette=pal_hex_lst, low=0, high=21)

                # # Init Plot
                # plot = Plot(x_range=Range1d(-1.1,1.1), y_range=Range1d(-1.1,1.1))
                # plot.title.text = "Graph Degree Centrality"

                # plot.add_tools(HoverTool(tooltips=[("index", "@index")]), TapTool(), BoxSelectTool(), ResetTool(), BoxZoomTool(), WheelZoomTool(), PanTool())

                # # Graph render
                # graph = from_networkx(G_symmetric, nx.spring_layout, scale=1, center=(0,0))

                # graph.node_renderer.glyph = Circle(size='node_size', fill_color={'field': 'node_color', 'transform': mapper})

                # graph.edge_renderer.glyph = MultiLine(line_color="#CCCCCC", line_alpha=0.8, line_width=1)
                # graph.edge_renderer.selection_glyph = MultiLine(line_color=Spectral4[2], line_width=1)
                # graph.edge_renderer.hover_glyph = MultiLine(line_color=Spectral4[1], line_width=1)

                # graph.selection_policy = NodesAndLinkedEdges()

                # plot.renderers.append(graph)

                # # Save and get div and script
                # script, div = components(plot) 
                # deg_cen_html.append({
                #     'div' : div,
                #     'script' : script
                # })
                # with open(dir_riwayat+'/deg_cen_html.json', 'w') as outfile:
                #     json.dump(deg_cen_html, outfile) # save html part Graph
                
                deg_cen = sort_and_small_dict(deg_cen, 100) # sort hasil jadi 100 besar utl tabel
                with open(dir_riwayat+"/deg_cen.json", 'w') as outfile:
                    json.dump(deg_cen, outfile) # Save deg cen tabel
                deg_cen = centrality_to_str_arr(deg_cen, dir_riwayat+"/relations.json")
            else: # Jika sudah tersedia
                # with open(dir_riwayat+"/deg_cen_html.json") as openfile:
                #     deg_cen_html = json.load(openfile) # load data json Graph
                with open(dir_riwayat+"/deg_cen.json") as openfile:
                    deg_cen = json.load(openfile) # load data json tabel
                deg_cen = centrality_to_str_arr(deg_cen, dir_riwayat+"/relations.json")
            
            # Degree centrality Twitter
            if not os.path.exists(dir_riwayat+"/deg_cen_tw.json") :
                G_symmetric = nx.Graph()
                relations = []

                with open(dir_relation_tw) as openfile: # open file relations.json
                    relations = json.load(openfile)

                for edge in relations:
                    G_symmetric.add_edge(edge['node1'], edge['node2'])

                deg_cen_tw = nx.degree_centrality(G_symmetric)

                deg_cen_tw = sort_and_small_dict(deg_cen_tw, 100) # sort hasil jadi 100 besar utl tabel
                with open(dir_riwayat+"/deg_cen_tw.json", 'w') as outfile:
                    json.dump(deg_cen_tw, outfile) # Save deg cen tabel
                deg_cen_tw = centrality_to_str_arr(deg_cen_tw, dir_riwayat+"/relations_tweet.json")
            else: # Jika sudah tersedia
                # with open(dir_riwayat+"/deg_cen_tw_html.json") as openfile:
                #     deg_cen_tw_html = json.load(openfile) # load data json Graph
                with open(dir_riwayat+"/deg_cen_tw.json") as openfile:
                    deg_cen_tw = json.load(openfile) # load data json tabel
                deg_cen_tw = centrality_to_str_arr(deg_cen_tw, dir_riwayat+"/relations_tweet.json")
            
            # Closeness centrality
            if not os.path.exists(dir_riwayat+"/clo_cen.json") :
                G_symmetric = nx.Graph()
                relations = []

                with open(dir_relation) as openfile: # open file relations.json
                    relations = json.load(openfile)

                for edge in relations:
                    G_symmetric.add_edge(edge['node1'], edge['node2'])

                clo_cen = nx.closeness_centrality(G_symmetric)
                
                # # Set node size and color
                # node_size = {k:100*v for k, v in clo_cen.items()}
                # node_color = {k:15*v for k, v in clo_cen.items()}

                # clo_cen_sort = sort_and_small_dict(clo_cen, 5)
                # for i in clo_cen.items():
                #     if i[1] < clo_cen_sort[4][1]: # menghapus node yg skornya kurang dari 0.1
                #         G_symmetric.remove_node(i[0])

                # # Set node attribute
                # nx.set_node_attributes(G_symmetric, node_color, 'node_color')
                # nx.set_node_attributes(G_symmetric, node_size, 'node_size')

                # # Map cubehelix_palette (Untuk Warna)
                # palette = sns.cubehelix_palette(21)
                # pal_hex_lst = palette.as_hex()

                # mapper = LinearColorMapper(palette=pal_hex_lst, low=0, high=21)

                # # Init Plot
                # plot = Plot(x_range=Range1d(-1.1,1.1), y_range=Range1d(-1.1,1.1))
                # plot.title.text = "Graph Closeness Centrality"

                # plot.add_tools(HoverTool(tooltips=[("index", "@index")]), TapTool(), BoxSelectTool(), ResetTool(), BoxZoomTool(), WheelZoomTool(), PanTool())

                # # Graph render
                # graph = from_networkx(G_symmetric, nx.spring_layout, scale=1, center=(0,0))

                # graph.node_renderer.glyph = Circle(size='node_size', fill_color={'field': 'node_color', 'transform': mapper})

                # graph.edge_renderer.glyph = MultiLine(line_color="#CCCCCC", line_alpha=0.8, line_width=1)
                # graph.edge_renderer.selection_glyph = MultiLine(line_color=Spectral4[2], line_width=1)
                # graph.edge_renderer.hover_glyph = MultiLine(line_color=Spectral4[1], line_width=1)

                # graph.selection_policy = NodesAndLinkedEdges()

                # plot.renderers.append(graph)

                # # Save and get div and script
                # script, div = components(plot) 
                # clo_cen_html.append({
                #     'div' : div,
                #     'script' : script
                # })
                # with open(dir_riwayat+'/clo_cen_html.json', 'w') as outfile:
                #     json.dump(clo_cen_html, outfile) # save html part Graph
                
                clo_cen = sort_and_small_dict(clo_cen, 100) # filter 100 besar
                with open(dir_riwayat+"/clo_cen.json", 'w') as outfile:
                    json.dump(clo_cen, outfile) # Save clo cen tabel
                clo_cen = centrality_to_str_arr(clo_cen, dir_riwayat+"/relations.json")
            else:
                # with open(dir_riwayat+"/clo_cen_html.json") as openfile:
                #     clo_cen_html = json.load(openfile) # save data json graph
                with open(dir_riwayat+"/clo_cen.json") as openfile:
                    clo_cen = json.load(openfile) # save data tabel
                clo_cen = centrality_to_str_arr(clo_cen, dir_riwayat+"/relations.json")
            
            # Closeness centrality Twitter
            if not os.path.exists(dir_riwayat+"/clo_cen_tw.json") :
                G_symmetric = nx.Graph()
                relations = []

                with open(dir_relation_tw) as openfile: # open file relations.json
                    relations = json.load(openfile)

                for edge in relations:
                    G_symmetric.add_edge(edge['node1'], edge['node2'])

                clo_cen_tw = nx.closeness_centrality(G_symmetric)
                
                clo_cen_tw = sort_and_small_dict(clo_cen_tw, 100) # filter 100 besar
                with open(dir_riwayat+"/clo_cen_tw.json", 'w') as outfile:
                    json.dump(clo_cen_tw, outfile) # Save clo cen tabel
                clo_cen_tw = centrality_to_str_arr(clo_cen_tw, dir_riwayat+"/relations_tweet.json")
            else:
                # with open(dir_riwayat+"/clo_cen_tw_html.json") as openfile:
                #     clo_cen_tw_html = json.load(openfile) # save data json graph
                with open(dir_riwayat+"/clo_cen_tw.json") as openfile:
                    clo_cen_tw = json.load(openfile) # save data tabel
                clo_cen_tw = centrality_to_str_arr(clo_cen_tw, dir_riwayat+"/relations_tweet.json")
            
            # Eigenvector centrality
            if not os.path.exists(dir_riwayat+"/eig_cen.json") :
                G_symmetric = nx.Graph()
                relations = []

                with open(dir_relation) as openfile: # open file relations.json
                    relations = json.load(openfile)

                for edge in relations:
                    G_symmetric.add_edge(edge['node1'], edge['node2'])
                    
                eig_cen = nx.eigenvector_centrality(G_symmetric)
                
                # # Set node size and color
                # node_size = {k:100*v for k, v in eig_cen.items()}
                # node_color = {k:15*v for k, v in eig_cen.items()}

                # for i in eig_cen.items():
                #     if i[1] < 0.1: # menghapus node yg skornya kurang dari 0.1
                #         G_symmetric.remove_node(i[0])

                # # Set node attribute
                # nx.set_node_attributes(G_symmetric, node_color, 'node_color')
                # nx.set_node_attributes(G_symmetric, node_size, 'node_size')

                # # Map cubehelix_palette (Untuk Warna)
                # palette = sns.cubehelix_palette(21)
                # pal_hex_lst = palette.as_hex()

                # mapper = LinearColorMapper(palette=pal_hex_lst, low=0, high=21)

                # # Init Plot
                # plot = Plot(x_range=Range1d(-1.1,1.1), y_range=Range1d(-1.1,1.1))
                # plot.title.text = "Graph Eigenvector Centrality"

                # plot.add_tools(HoverTool(tooltips=[("index", "@index")]), TapTool(), BoxSelectTool(), ResetTool(), BoxZoomTool(), WheelZoomTool(), PanTool())

                # # Graph render
                # graph = from_networkx(G_symmetric, nx.spring_layout, scale=1, center=(0,0))

                # graph.node_renderer.glyph = Circle(size='node_size', fill_color={'field': 'node_color', 'transform': mapper})

                # graph.edge_renderer.glyph = MultiLine(line_color="#CCCCCC", line_alpha=0.8, line_width=1)
                # graph.edge_renderer.selection_glyph = MultiLine(line_color=Spectral4[2], line_width=1)
                # graph.edge_renderer.hover_glyph = MultiLine(line_color=Spectral4[1], line_width=1)

                # graph.selection_policy = NodesAndLinkedEdges()

                # plot.renderers.append(graph)

                # # Save and get div and script
                # script, div = components(plot) 
                # eig_cen_html.append({
                #     'div' : div,
                #     'script' : script
                # })
                # with open(dir_riwayat+'/eig_cen_html.json', 'w') as outfile:
                #     json.dump(eig_cen_html, outfile) # save html part Graph
                
                eig_cen = sort_and_small_dict(eig_cen, 100) # filter 100 besar
                with open(dir_riwayat+"/eig_cen.json", 'w') as outfile:
                    json.dump(eig_cen, outfile) # Save eig cen
                eig_cen = centrality_to_str_arr(eig_cen, dir_riwayat+"/relations.json")
                
            else:
                # with open(dir_riwayat+"/eig_cen_html.json") as openfile:
                #     eig_cen_html = json.load(openfile) # save data graph
                with open(dir_riwayat+"/eig_cen.json") as openfile:
                    eig_cen = json.load(openfile) # save data tabel
                eig_cen = centrality_to_str_arr(eig_cen, dir_riwayat+"/relations.json")
            
            # Eigenvector centrality Twitter
            if not os.path.exists(dir_riwayat+"/eig_cen_tw.json") :
                G_symmetric = nx.Graph()
                relations = []

                with open(dir_relation_tw) as openfile: # open file relations.json
                    relations = json.load(openfile)

                for edge in relations:
                    G_symmetric.add_edge(edge['node1'], edge['node2'])
                    
                eig_cen_tw = nx.eigenvector_centrality(G_symmetric)
                
                eig_cen_tw = sort_and_small_dict(eig_cen_tw, 100) # filter 100 besar
                with open(dir_riwayat+"/eig_cen_tw.json", 'w') as outfile:
                    json.dump(eig_cen_tw, outfile) # Save eig cen
                eig_cen_tw = centrality_to_str_arr(eig_cen_tw, dir_riwayat+"/relations_tweet.json")
                
            else:
                # with open(dir_riwayat+"/eig_cen_tw_html.json") as openfile:
                #     eig_cen_tw_html = json.load(openfile) # save data graph
                with open(dir_riwayat+"/eig_cen_tw.json") as openfile:
                    eig_cen_tw = json.load(openfile) # save data tabel
                eig_cen_tw = centrality_to_str_arr(eig_cen_tw, dir_riwayat+"/relations_tweet.json")

            # deg_cen = centrality_to_str_arr(deg_cen)
            # clo_cen = centrality_to_str_arr(clo_cen)
            # bet_cen = centrality_to_str_arr(bet_cen)
            # eig_cen = centrality_to_str_arr(eig_cen)

            # show raw data post ig dan tw
            raw_data = []
            with open(dir_riwayat+"/posts.json") as openfile:
                raw_data = json.load(openfile)
            raw_data_tw = []
            with open(dir_riwayat+"/tweet_tag.json") as tw_data:
                raw_data_tw = json.load(tw_data)
            ig_profil = []
            with open(dir_riwayat+'/profil.json') as f:
                data = json.load(f)
                for line in data:
                    ig_profil.append("https://www.instagram.com/"+line['profil_name']+"/")
            ig_profil = list(dict.fromkeys(ig_profil)) # return list tanpa duplikat
            tw_profil = []
            with open(dir_riwayat+'/tw_profil.json') as tw_f:
                tw_profil = json.load(tw_f)
            
            waktu = (time.time() - start_time) # Hitung waktu proses
            waktu_filter = divmod(waktu, 60)
            menit = waktu_filter[0]
            detik = waktu_filter[1]

            cut_date = os.path.basename(dir_riwayat).split("_")
            day = cut_date[2]
            month = cut_date[3]
            year = cut_date[4]

            return render_template('index.html', status='proses', tag=riwayat+"_"+str(day)+"/"+str(month)+"/"+str(year), n_nodes=f'{n_nodes:,d}', n_edges=f'{n_edges:,d}', raw_data=raw_data, data_tw=raw_data_tw, profil_ig=ig_profil, profil_tw=tw_profil, tag_html=tag_html, bet_cen=bet_cen, deg_cen=deg_cen, clo_cen=clo_cen, eig_cen=eig_cen,  menit=f'{menit:.0f}', detik=f'{detik:.2f}', n_nodes_tw=f'{n_nodes_tw:,d}', n_edges_tw=f'{n_edges_tw:,d}', tag_html_tw=tag_html_tw, bet_cen_tw=bet_cen_tw,  deg_cen_tw=deg_cen_tw, clo_cen_tw=clo_cen_tw, eig_cen_tw=eig_cen_tw)
        else:
            return jsonify("Isian Kosong")

    dir_data = os.path.join(BASEDIR, "data")
    riwayat = []
    for folder in os.listdir(dir_data):
        x = folder.split("_")
        # hourday = x[1]
        # xmonth = x[2]
        # xyear = x[3]
        # y = hourday.split(" ")
        # yday = y[1]

        riwayat.append(x[0]+"_"+x[1])
    
    riwayat.sort(reverse=True)
    
    # return jsonify(riwayat)
    return render_template('index.html', riwayat=riwayat, status='home')

# Route Update Proses


# Route Delete Hashtag Data
@app.route('/delete_riwayat', methods=['POST'])
def delete_riwayat():
    if request.method == 'POST':
        id_riwayat = request.form['del_tag']

        # remove old folder
        dir_data = os.path.join(BASEDIR, "data")
        for x in os.listdir(dir_data):
            if id_riwayat in x:
                shutil.rmtree(os.path.join(dir_data, x))
                print(id_riwayat, "dihapus")
        return redirect(url_for('cari'))
    else:
        print("Getback!")

# Run Server
if __name__ == '__main__':
    app.run(debug=True, port=5000)