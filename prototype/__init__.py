from flask import Flask, request
from flask_cors import CORS
import datetime
from flask import render_template
import requests

app = Flask(__name__)
CORS(app)
global tokenID
tokenID = 0

def createMetadata(grade, img):
    url = "https://metadata-api.klaytnapi.com/v1/metadata"
    payload = {
        "metadata": {
            "description": "Beef NFT는 AI 소고기 등급 판별기를 통해 발행된 NFT로 AI 기반으로 소고기 이미지를 통해 소고기의 등급을 판별한 후 판별된 등급을 NFT에 저장해 인증서를 발급한다.",
            "external_url": "https://beef.honeyvuitton.com/", 
            "image": img, 
            "name": "Beef NFT",
            "attributes": [ {"grdade" : grade}, {"createdTime": str(datetime.datetime.now())},], 
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

    return response.json()

def mintNFT(uri, tokenID):
    url = "https://kip17-api.klaytnapi.com/v1/contract/0xe3a390fdb12dafe2eb37d7829d11a18f37e59424/token"

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

@app.route('/test', methods = ['POST'])

def API():
    params = request.get_json()
    print(params,type(params))
    if params["grade"]:
        metaURI = createMetadata(params["grade"],params["img"])
        return metaURI
        # global tokenID
        # tokenID += 1
        # result = mintNFT(metaURI,str(tokenID)+str(datetime.datetime.today().year)[2:])
        # return result
    else:
        return params

@app.route("/")
def intro():
    return render_template('index.html')
