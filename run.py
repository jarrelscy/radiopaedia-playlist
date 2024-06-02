import requests
from bs4 import BeautifulSoup
import shutil
import os
from tqdm import tqdm_notebook as tqdm
from PIL import Image,ImageDraw,ImageFont
from matplotlib import pyplot as plt
import img2pdf
from io import BytesIO
import multiprocessing
def processSlide(href, index):
    doc = requests.get('https://radiopaedia.org' + href).text
    soup = BeautifulSoup(doc, 'html.parser')
    src = soup.select('div.slide img')[0]['src']    
    response = requests.get(src)
    im=Image.open(BytesIO(response.content))
    w,h=im.size
    im = im.resize((1000,h*1000//w), Image.BICUBIC)    
    if len(im.split()) == 4:
        background = Image.new("RGB", im.size, (255, 255, 255))
        background.paste(im, mask=im.split()[3]) # 3 is the alpha channel
        background.save(base+'/'+str(index) + '_'+src.split('/')[-1] +'.jpeg')
    else:
        im.save(base+'/'+str(index) + '_'+src.split('/')[-1] +'.jpeg')
def processCase(href, index):
    doc = requests.get('https://radiopaedia.org' + href).text
    soup = BeautifulSoup(doc, 'html.parser')
    if len(soup.select('.caseNumber')) == 0:
        #probably a hidden case - do nothing
        raise Exception('hidden playlist')
    else:
        src = soup.select('.caseNumber')[0].text    
        link = soup.select('.caseNumber')[0]['href']    
        doc = requests.get('https://radiopaedia.org' + link).text
        soup = BeautifulSoup(doc, 'html.parser')

        try:
            author = soup.select('div.author-info > a')[0].text    
        except:
            print (src, 'https://radiopaedia.org' + link)
            author = None

        title = soup.select('h1')[0].text.replace('/',' ').replace('\\', ' ')  
        if author == None: title = 'PRIVATE CASE'    
        title_write = ''
        for word in title.split(' '):        
            if (len(title_write)+len(word)) > 43 and '\n' not in title_write:
                title_write+='\n'
            title_write+=word+' '
        img = Image.open("blank.jpg")
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype("ss.ttf", 50)
        sfont = ImageFont.truetype("ss.ttf", 40)    

        draw.text((100, 100),str(title_write),(0,0,0),font=font)
        if author != None:
            draw.text((100, 225),str(author)+', rID: '+str(src),(0,0,0),font=sfont)
            draw.text((100, 350),'NOTES:',(0,0,0),font=font)    
        img = img.resize((1000,750), Image.LANCZOS)
        img.save(base+'/'+str(index) + '_'+ str(title.encode('ascii', 'ignore')) +'.jpeg')
        return img
    
def process(d):   
    i,url = d
    if 'slide' in url:
        processSlide(url, i)
    if 'case' in url:
        processCase(url, i)


# your list of publicly available radiopaedia playlists 

urls = ['https://radiopaedia.org/playlists/ea0f69d646dfb88b8cb8671d4fb4fc73',
       'https://radiopaedia.org/playlists/8280c0135f69acd1b2d27b8e335aa46d',
       'https://radiopaedia.org/playlists/c149d70e31c045a948a81e2c83a1ca9c',
       'https://radiopaedia.org/playlists/bd41d362e87fd61efd0b9a78d4d3b692']

for url in urls:
    base = url.split('/')[-1]         
    if os.path.exists(base+".pdf"):
        print (base)
        continue
    html_doc = requests.get(url).text
    soup = BeautifulSoup(html_doc, 'html.parser')
    if not os.path.exists(base):
        os.mkdir(base)
    else:
        for file in os.listdir(base):
            os.remove(os.path.join(base,file))

    print (url)
    print ('Now downloading ... please wait')
    urls = [[i,t['href']] for i,t in enumerate(list(soup.select("div.playlist-entry > a.thumbnail")))]
    debug=False
    if not debug:
        pool = multiprocessing.Pool(processes=10)
        list(tqdm(pool.imap(process, urls), total=len(urls)))
    else:
        for url in tqdm(urls):
            process(url)
    print ('Downloaded')

    files = [os.path.join(base,p) for p in sorted(os.listdir(base), key=lambda x:int(x.split('_')[0]))]
    pdf_bytes = img2pdf.convert(files)
    file = open(base+".pdf","wb")
    file.write(pdf_bytes)
