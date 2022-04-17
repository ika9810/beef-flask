from flask import Flask, request, jsonify
from flask_cors import CORS
import datetime
import time
from flask import render_template
import requests
import re
######################AI MODEL###########################
from sklearn.decomposition import PCA

import numpy as np
from PIL import Image
import joblib
from io import BytesIO
import base64
#########################################################

app = Flask(__name__)
CORS(app)

######################AI MODEL###########################
def evaluate_grade(img):
    # path = './prototype/static/img/image.jpeg'
    # image_pil = Image.open(path)
    #https://stackoverflow.com/questions/26070547/decoding-base64-from-post-to-use-in-pil base64 Image 활용
    image_pil = Image.open(BytesIO(base64.b64decode(img)))
    image = np.array(image_pil)

    xaverage=image.shape[0]
    yaverage=image.shape[1]
    #한변의 길이의 절반
    halfpicsize=150

    #target이미지가 원본사진을 이탈하는것 방지
    if yaverage<halfpicsize+10:
        yaverage=halfpicsize+10
    elif yaverage>len(image)-(halfpicsize+10):
        yaverage=len(image)-(halfpicsize+10)

    if xaverage<(halfpicsize+10):
        xaverage=(halfpicsize+10)
    elif xaverage>len(image[0])-(halfpicsize+10):
        xaverage=len(image[0])-(halfpicsize+10)


    #300*300 cutting    
    cutimage=image_pil.crop((xaverage-halfpicsize,yaverage-halfpicsize,xaverage+halfpicsize,yaverage+halfpicsize))
    #300*300=>50*50 resizing
    resizedcutimage=np.array(cutimage.resize((50,50),Image.LANCZOS))
    #3차원=>2차원
    resizedcutimage=np.concatenate(resizedcutimage)
    #2차원=>1차원
    resizedcutimage=np.concatenate(resizedcutimage)

    #target 데이터 저장
    j=[]
    j.append(resizedcutimage)
    
     
    #300*300 target cutting기준
    #K-neighbor모델을 위한 pca모델
    pca31=joblib.load('./prototype/static/ai_model/pca_component31.pkl')
    
    #target data 변환
    #K-neighbor 전용
    k=pca31.transform(j)
    j=[]
    
   
    
    #모델 불러오기
    loaded_kn15_model=joblib.load( './prototype/static/ai_model/pca_knn_neighbor15.pkl')

    #print("KN-15모델 예측")
    #print(loaded_kn15_model.predict(k))
    #print(loaded_kn15_model.classes_)
    #print(loaded_kn15_model.predict_proba(k))
    
    result=[]
    
    for i in range(5):
        newdict={}
        newdict["className"]=loaded_kn15_model.classes_[i]
        newdict["probability"]=loaded_kn15_model.predict_proba(k)[0][i]
        result.append(newdict)
    return result

######################메타데이터 생성하기###########################
def createMetadata(grade, img):
    url = "https://metadata-api.klaytnapi.com/v1/metadata"
    payload = {
        "metadata": {
            "description": "Beef NFT는 AI 소고기 등급 판별기를 통해 발행된 NFT로 AI 기반으로 소고기 이미지를 통해 소고기의 등급을 판별한 후 판별된 등급을 NFT에 저장해 인증서를 발급한다.",
            "external_url": "https://beef.honeyvuitton.com/", 
            "image": img, 
            "name": "Beef NFT",
            #Opensea에서 property 에 등록될 수 있는 형식으로 바꾸어 줬고, NFT의 생성일자도 birthday형식으로 지정했는데 이 때 unix timestamp형식이 필요해서 해당 형식에 맞게 진행하였다.
            "attributes": [{
                "display_type": "date",
                "trait_type": "Birthday",
                "value": str(time.time()),
            },
            {
                "trait_type": "grade",
                "value": grade
            },]
        },
        # "filename": "test.json"
    }
    headers = {
        "x-chain-id": "1001",
        "Authorization": "Basic S0FTS0wyQlMxRDFJMUczREowRTdFUDhEOmptd2hlNkZrcXZLLWxheTUxWHJ5QktJVFJPaXE5MUtyRE9OMjFxR0Q=",
        "Content-Type": "application/json"
    }

    response = requests.request("POST", url, json=payload, headers=headers)
    # {
    # "contentType": "application/json",
    # "filename": "13126799-5d29-06f8-ea1d-ff5f5165ce35.json",
    # "uri": "https://metadata-store.klaytnapi.com/9c7de118-cf48-8ab5-f186-4ed29b9cf6b7/13126799-5d29-06f8-ea1d-ff5f5165ce35.json"
    # }     //KAS Medata API 메타데이터 생성 부분 리턴 형태

    return response.json()["uri"]

def mintNFT(uri, tokenID):
    url = "https://kip17-api.klaytnapi.com/v1/contract/0xe3a390fdb12dafe2eb37d7829d11a18f37e59424/token" #beefcoin
    #url = "https://kip17-api.klaytnapi.com/v1/contract/0xe966c58075372c9ddeb2d07080075f32d053f463/token" #maidcat
    

    payload = {
        "to": "0x24b2803c34b11740acd0cc35648e34163c5cba0c",
        "id": tokenID,
        "uri": uri,
    }
    headers = {
        "x-chain-id": "1001",
        "Authorization": "Basic S0FTS0wyQlMxRDFJMUczREowRTdFUDhEOmptd2hlNkZrcXZLLWxheTUxWHJ5QktJVFJPaXE5MUtyRE9OMjFxR0Q=",
        "Content-Type": "application/json"
    }

    response = requests.request("POST", url, json=payload, headers=headers)
    return response.json()

@app.route('/nftMint', methods = ['POST'])

def MINT():
    params = request.get_json()
    #print(params,type(params))
    if params["grade"]:
        metaURI = createMetadata(params["grade"],params["img"])
        #KAS에서 토큰을 발행할 때 토큰 아이디는 무조건 16진수여야 한다 현재시간을 일렬로 정수형만 추출해 16진수로 변환시켜서 호출한다.
        hex_tokenID = hex(int('0x'+re.sub(r'[^0-9]', '',str(datetime.datetime.now())),16))
        print(hex_tokenID)
        result = mintNFT(metaURI,hex_tokenID)
        print(result)
        return result
    else:
        return params

@app.route('/predict', methods = ['POST'])

def ai():
    params = request.get_json()

    result = evaluate_grade(params['img'])
    #########################json 형식으로 리턴하기 위해 jsonify 함수 사용
    return jsonify(result)

@app.route("/")
def intro():
    return render_template('index.html')
