from user_agent import generate_user_agent
from SignerPy import *
import requests, SignerPy, json, secrets, uuid, binascii, os, time, random,re
class TikTok:
    @staticmethod
    def xor(string):
          return "".join([hex(ord(c) ^ 5)[2:] for c in string])
    def GetUser(self,es):
        secret = secrets.token_hex(16)
        xor_email=self.xor(es)
        params = {
            "request_tag_from": "h5",
            "fixed_mix_mode": "1",
            "mix_mode": "1",
            "account_param": xor_email,
            "scene": "1",
            "device_platform": "android",
            "os": "android",
            "ssmix": "a",
            "type": "3736",
            "_rticket": str(round(random.uniform(1.2, 1.6) * 100000000) * -1) + "4632",
            "cdid": str(uuid.uuid4()),
            "channel": "googleplay",
            "aid": "1233",
            "app_name": "musical_ly",
            "version_code": "370805",
            "version_name": "37.8.5",
            "manifest_version_code": "2023708050",
            "update_version_code": "2023708050",
            "ab_version": "37.8.5",
            "resolution": "1600*900",
            "dpi": "240",
            "device_type": "SM-G998B",
            "device_brand": "samsung",
            "language": "en",
            "os_api": "28",
            "os_version": "9",
            "ac": "wifi",
            "is_pad": "0",
            "current_region": "TW",
            "app_type": "normal",
            "sys_region": "US",
            "last_install_time": "1754073240",
            "mcc_mnc": "46692",
            "timezone_name": "Asia/Baghdad",
            "carrier_region_v2": "466",
            "residence": "TW",
            "app_language": "en",
            "carrier_region": "TW",
            "timezone_offset": "10800",
            "host_abi": "arm64-v8a",
            "locale": "en-GB",
            "ac2": "wifi",
            "uoo": "1",
            "op_region": "TW",
            "build_number": "37.8.5",
            "region": "GB",
            "ts":str(round(random.uniform(1.2, 1.6) * 100000000) * -1),
            "iid": str(random.randint(1, 10**19)),
            "device_id": str(random.randint(1, 10**19)),
            "openudid": str(binascii.hexlify(os.urandom(8)).decode()),
            "support_webview": "1",
            "okhttp_version": "4.2.210.6-tiktok",
            "use_store_region_cookie": "1",
            "app_version":"37.8.5"}
        cookies = {
            "passport_csrf_token": secret,
            "passport_csrf_token_default": secret,
            "install_id": params["iid"],
        }
        
        
        
        
        s=requests.session()
        cookies = {
            '_ga_3DVKZSPS3D': 'GS2.1.s1754435486$o1$g0$t1754435486$j60$l0$h0',
            '_ga': 'GA1.1.504663773.1754435486',
            '__gads': 'ID=0cfb694765742032:T=1754435487:RT=1754435487:S=ALNI_MbIZNqLgouoeIxOQ2-N-0-cjxxS1A',
            '__gpi': 'UID=00001120bc366066:T=1754435487:RT=1754435487:S=ALNI_MaWgWYrKEmStGHPiLiBa1zlQOicuA',
            '__eoi': 'ID=22d520639150e74a:T=1754435487:RT=1754435487:S=AA-AfjZKI_lD2VnwMipZE8ienmGW',
            'FCNEC': '%5B%5B%22AKsRol8AtTXetHU2kYbWNbhPJd-c3l8flgQb4i54HStVK8CCEYhbcA3kEFqWYrBZaXKWuO9YYJN53FddyHbDf05q1qY12AeNafjxm2SPp7mhXZaop_3YiUwuo_WHJkehVcl5z4VyD7GHJ_D8nI2DfTX5RfrQWIHNMA%3D%3D%22%5D%5D',
        }
        
        headers = {
            'accept': '*/*',
            'accept-language': 'en,ar;q=0.9,en-US;q=0.8',
            'application-name': 'web',
            'application-version': '4.0.0',
            'content-type': 'application/json',
            'origin': 'https://temp-mail.io',
            'priority': 'u=1, i',
            'referer': 'https://temp-mail.io/',
            'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
            'x-cors-header': 'iaWg3pchvFx48fY',
        }
        
        json_data = {
            'min_name_length': 10,
            'max_name_length': 10,
        }
        
        response = requests.post('https://api.internal.temp-mail.io/api/v3/email/new', cookies=cookies, headers=headers, json=json_data)
        name=response.json()["email"]
        url = "https://api16-normal-c-alisg.tiktokv.com/passport/account_lookup/email/"
        s.cookies.update(cookies)
        m=SignerPy.sign(params=params,cookie=cookies)
        
        headers = {
          'User-Agent': "com.zhiliaoapp.musically/2023708050 (Linux; U; Android 9; en_GB; SM-G998B; Build/SP1A.210812.016;tt-ok/3.12.13.16)",
          'x-ss-stub':m['x-ss-stub'],
          'x-tt-dm-status': "login=1;ct=1;rt=1",
          'x-ss-req-ticket':m['x-ss-req-ticket'],
          'x-ladon': m['x-ladon'],
          'x-khronos': m['x-khronos'],
          'x-argus': m['x-argus'],
          'x-gorgon': m['x-gorgon'],
          'content-type': "application/x-www-form-urlencoded",
          'content-length': m['content-length'],
        
        }
        
        response = requests.post(url, headers=headers,params=params,cookies=cookies)
        
        if 'data' in response.json():
            try:passport_ticket=response.json()["data"]["accounts"][0]["passport_ticket"]
            except Exception as e:return {'status':e}
        else:
            return {'status':'Bad'}           
        
        name_xor=self.xor(name)
        url = "https://api16-normal-c-alisg.tiktokv.com/passport/email/send_code/"
        params.update({"not_login_ticket":passport_ticket,"email":name_xor})
        m = SignerPy.sign(params=params, cookie=cookies)
        headers = {
            'User-Agent': "com.zhiliaoapp.musically/2023708050 (Linux; U; Android 9; en_GB; SM-G998B; Build/SP1A.210812.016;tt-ok/3.12.13.16)",
            'Accept-Encoding': "gzip",
            'x-ss-stub': m['x-ss-stub'],
            'x-ss-req-ticket': m['x-ss-req-ticket'],
            'x-ladon': m['x-ladon'],
            'x-khronos': m['x-khronos'],
            'x-argus': m['x-argus'],
            'x-gorgon': m['x-gorgon'],
        }
        response = s.post(url, headers=headers, params=params, cookies=cookies)
        
        time.sleep(5)
        cookies = {
            '_ga': 'GA1.1.504663773.1754435486',
            '__gads': 'ID=0cfb694765742032:T=1754435487:RT=1754435487:S=ALNI_MbIZNqLgouoeIxOQ2-N-0-cjxxS1A',
            '__gpi': 'UID=00001120bc366066:T=1754435487:RT=1754435487:S=ALNI_MaWgWYrKEmStGHPiLiBa1zlQOicuA',
            '__eoi': 'ID=22d520639150e74a:T=1754435487:RT=1754435487:S=AA-AfjZKI_lD2VnwMipZE8ienmGW',
            'FCNEC': '%5B%5B%22AKsRol8AtTXetHU2kYbWNbhPJd-c3l8flgQb4i54HStVK8CCEYhbcA3kEFqWYrBZaXKWuO9YYJN53FddyHbDf05q1qY12AeNafjxm2SPp7mhXZaop_3YiUwuo_WHJkehVcl5z4VyD7GHJ_D8nI2DfTX5RfrQWIHNMA%3D%3D%22%5D%5D',
            '_ga_3DVKZSPS3D': 'GS2.1.s1754435486$o1$g0$t1754435503$j43$l0$h0',
        }
        
        headers = {
            'accept': '*/*',
            'accept-language': 'en,ar;q=0.9,en-US;q=0.8',
            'application-name': 'web',
            'application-version': '4.0.0',
            'content-type': 'application/json',
            'origin': 'https://temp-mail.io',
            'priority': 'u=1, i',
            'referer': 'https://temp-mail.io/',
            'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
            'x-cors-header': 'iaWg3pchvFx48fY'
        }
        
        response = requests.get(
            'https://api.internal.temp-mail.io/api/v3/email/{}/messages'.format(name),
            cookies=cookies,
            headers=headers,
        )
        import re
        try:
            exEm = response.json()[0]
            match = re.search(r"This email was generated for ([\w.]+)\.", exEm["body_text"])
            if match:
                username = match.group(1)
                print(username)
                return {'status':'Good','username':username,'Dev':'Mustafa','Telegram':'@PPH9P'}
        except Exception as e:return {'status':'Bad','Info':e,'Dev':'Mustafa','Telegram':'@PPH9P'}    
        #@staticmethod
 
    def GetInfo(self,username):
        try:
            headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
    };url = f"https://www.tiktok.com/@{username}";response = requests.get(url, headers=headers,timeout=10).text;data = response.split('''"userInfo":{"user":{''')[1].split('''</sc''')[0];followers = data.split('"followerCount":')[1].split(',')[0];id = data.split('"id":"')[1].split('"')[0];nickname = data.split('"nickname":"')[1].split('"')[0];following = data.split('"followingCount":')[1].split(',')[0];likes = data.split('"heart":')[1].split(',')[0];ff = {
    "🔥 HIT TIKTOK 🔥": {
        "User": username,
        "Name": nickname,
        "Id": id,
        "Followers": followers,
        "Following": following,
        "Likes": likes
    },
    "By": "@D_B_HH",
    "Channel": "@k_1_cc"
}
            return {
    "status": "Good",
    "Info": ff,
    "Dev": "Mustafa",
    "Telegram": "@PPH9P"
}
        except Exception as e:return {'status':'Bad','Dev':'Mustafa','Telegram':'@PPH9P'}
#
    def GetLevel(self, username):
        username = username.strip().lstrip('@')
        url = f'https://www.tiktok.com/@{username}'
        headers = {'User-Agent': str(generate_user_agent())}

        try:  
            response = requests.get(url, headers=headers)  
            if '{"userInfo":{' in response.text:  
         
                match = re.search(r'"userInfo":\{.*?"id":"([^"]+)"', response.text)  
                if match:  
                    user_id = match.group(1)  
            elif '"user":{"id":"' in response.text:  
                match = re.search(r'"user":{"id":"([^"]+)"', response.text)  
                if match:  
                    user_id = match.group(1)  
            else:
                user_id = None

            if not user_id:
                api_url = f"https://www.tikwm.com/api/user/info?unique_id={username}"  
                api_response = requests.get(api_url)  
                if api_response.status_code == 200:  
                    data = api_response.json()  
                    if data.get("code") == 0 and "data" in data:  
                        user_id = data["data"]["user"]["id"]  

            if not user_id:
                return None, None
            
            user_details, raw_response = self.get_tiktok_user_details(user_id)

            if user_details and user_details.get('status_code') == 0:  
                data = user_details.get('data', {})  
                badge_list = data.get('badge_list', [])  
                for badge in badge_list:  
                    combine = badge.get('combine', {})  
                    if combine and 'text' in combine:  
                        text_data = combine.get('text', {})  
                        if 'default_pattern' in text_data:  
                            aa = text_data.get('default_pattern')  
                            return {'status':'Good','Level':text_data['default_pattern'],'Dev':'Mustafa','Telegram':'@PPH9P'}
                return user_id, user_details  
            else:
                return {'status':'Bad','Dev':'Mustafa','Telegram':'@PPH9P'}
                
                return user_id, None  

        except Exception as e:  
            return e
            return {'status':'Bad','Info':e,'Dev':'Mustafa','Telegram':'@PPH9P'}  
            return None, None

    def get_tiktok_user_details(self, user_id, custom_headers=None, custom_params=None):

        url = "https://webcast22-normal-c-alisg.tiktokv.com/webcast/user/"

        headers = {  
            "Host": "webcast22-normal-c-alisg.tiktokv.com",  
            "cookie": "store-idc=alisg; passport_csrf_token=20e9da8b0e16abaa45d4ce2ad75a1325; passport_csrf_token_default=20e9da8b0e16abaa45d4ce2ad75a1325; d_ticket=913261767c3f16148c133796e661c1d83cf5d; multi_sids=7464926696447099909%3A686e699e8bbbc4e9f5e08d31c038c8e4; odin_tt=e2d5cd703c2e155d572ad323d28759943540088ddc6806aa9a9b48895713be4b585e78bf3eb17d28fd84247c4198ab58fab17488026468d3dde38335f4ab928ad1b9bd82a2fb5ff55da00e3368b4d215; cmpl_token=AgQQAPMsF-RPsLemUeAYPZ08_KeO5HxUv5IsYN75Vg; sid_guard=686e699e8bbbc4e9f5e08d31c038c8e4%7C1751310846%7C15552000%7CSat%2C+27-Dec-2025+19%3A14%3A06+GMT; uid_tt=683a0288ad058879bbc16d3b696fa815e1d72c050bdb2d14b824141806068417; uid_tt_ss=683a0288ad058879bbc16d3b696fa815e1d72c050bdb2d14b824141806068417; sid_tt=686e699e8bbbc4e9f5e08d31c038c8e4; sessionid=686e699e8bbbc4e9f5e08d31c038c8e4; sessionid_ss=686e699e8bbbc4e9f5e08d31c038c8e4; store-country-code=eg; store-country-code-src=uid; tt-target-idc=alisg; ttwid=1%7Cmdx9QyT3L35S3CFNpZ_6a1mG2Q3hbfWvwQh6gY5hjhw%7C1751310949%7C253ef523ddc8960c5f52b286d8ce0afc2623ec081a777dac3ba5606ecdc1bd40; store-country-sign=MEIEDPH3p6xlgJXYVovbBgQgMf22gnCf0op7iOSSy6oKKB7paF60OVLAsxbGkh6BUGAEEF0aMxzItZZ03IrkjedsuYY; msToken=Srtgt7p6ncYXI8gph0ecExfl9DpgLtzOynFNZjVGLkKUjqV0J1JI8aBoE8ERmO5f43HQhtJxcU2FeJweSbFIlIOADOHP_z75VvNeA2hp5LN1JZsKgj-wymAdEVJt",  
            "x-tt-pba-enable": "1",  
            "x-bd-kmsv": "0",  
            "x-tt-dm-status": "login=1;ct=1;rt=1",  
            "live-trace-tag": "profileDialog_batchRequest",  
            "sdk-version": "2",  
            "x-tt-token": "034865285659c6477b777dec3ab5cd0aa70363599c1acde0cd4e911a51fed831bdb2ec80a9a379e8e66493471e519ccf05287299287a55f0599a72988865752a3668a1a459177026096896cf8d50b6e8b5f4cec607bdcdee5a5ce407e70ce91d52933--0a4e0a20da4087f3b0e52a48822384ac63e937da36e5b0ca771f669a719cf633d66f8aed12206a38feb1f115b80781d5cead8068600b779eb2bba6c09d8ae1e6a7bc44b46b931801220674696b746f6b-3.0.0",  
            "passport-sdk-version": "6031490",  
            "x-vc-bdturing-sdk-version": "2.3.8.i18n",  
            "x-tt-request-tag": "n=0;nr=011;bg=0",  
            "x-tt-store-region": "eg",  
            "x-tt-store-region-src": "uid",  
            "rpc-persist-pyxis-policy-v-tnc": "1",  
            "x-ss-dp": "1233",  
            "x-tt-trace-id": "00-c24dca7d1066c617d7d3cb86105004d1-c24dca7d1066c617-01",  
            "user-agent": "com.zhiliaoapp.musically/2023700010 (Linux; U; Android 11; ar; SM-A105F; Build/RP1A.200720.012; Cronet/TTNetVersion:f6248591 2024-09-11 QuicVersion:182d68c8 2024-05-28)",  
            "accept-encoding": "gzip, deflate, br",  
            "x-tt-dataflow-id": "671088640"  
        }  

        if custom_headers:
            headers.update(custom_headers)  
  
        params = {  
            "user_role": '{"7464926696447099909":1,"7486259459669820432":1}',  
            "request_from": "profile_card_v2",  
            "sec_anchor_id": "MS4wLjABAAAAiwBH59yM2i_loS11vwxZsudy4Bsv5L_EYIkYDmxgf-lv3oZL4YhQCF5oHQReiuUV",  
            "request_from_scene": "1",  
            "need_preload_room": "false",  
            "target_uid": user_id,  
            "anchor_id": "246047577136308224",  
            "packed_level": "2",  
            "need_block_status": "true",  
            "current_room_id": "7521794357553400594",  
            "device_platform": "android",  
            "os": "android",  
            "ssmix": "a",  
            "_rticket": "1751311566864",  
            "cdid": "808876f8-7328-4885-857d-8f15dd427861",  
            "channel": "googleplay",  
            "aid": "1233",  
            "app_name": "musical_ly",  
            "version_code": "370001",  
            "version_name": "37.0.1",  
            "manifest_version_code": "2023700010",  
            "update_version_code": "2023700010",  
            "ab_version": "37.0.1",  
            "resolution": "720*1382",  
            "dpi": "280",  
            "device_type": "SM-A105F",  
            "device_brand": "samsung",  
            "language": "ar",  
            "os_api": "30",  
            "os_version": "11",  
            "ac": "wifi",  
            "is_pad": "0",  
            "current_region": "IQ",  
            "app_type": "normal",  
            "sys_region": "IQ",  
            "last_install_time": "1751308971",  
            "timezone_name": "Asia/Baghdad",  
            "residence": "IQ",  
            "app_language": "ar",  
            "timezone_offset": "10800",  
            "host_abi": "armeabi-v7a",  
            "locale": "ar",  
            "content_language": "ar,",  
            "ac2": "wifi",  
            "uoo": "1",  
            "op_region": "IQ",  
            "build_number": "37.0.1",  
            "region": "IQ",  
            "ts": "1751311566",  
            "iid": "7521814657976928001",  
            "device_id": "7405632852996097552",  
            "openudid": "c79c40b21606bf59",  
            "webcast_sdk_version": "3610",  
            "webcast_language": "ar",  
            "webcast_locale": "ar_IQ",  
            "es_version": "3",  
            "effect_sdk_version": "17.6.0",  
            "current_network_quality_info": '{"tcp_rtt":16,"quic_rtt":16,"http_rtt":584,"downstream_throughput_kbps":1400,"quic_send_loss_rate":-1,"quic_receive_loss_rate":-1,"net_effective_connection_type":3,"video_download_speed":1341}'  
        }  

        if custom_params: 
            params.update(custom_params)  

        try:  
            up = get(params=params)  
            def parse_cookie_string(cookie_string):  
                cookie_dict = {}  
                for item in cookie_string.split(';'):  
                    if item.strip():  
                        try:  
                            key, value = item.strip().split('=', 1)  
                            cookie_dict[key.strip()] = value.strip()  
                        except ValueError:  
                            cookie_dict[item.strip()] = ''  
                return cookie_dict  
            cookie_dict = parse_cookie_string(headers["cookie"])  
            sg = sign(params=up, cookie=cookie_dict)  

            headers.update({  
                'x-ss-req-ticket': sg['x-ss-req-ticket'],  
                'x-ss-stub': sg['x-ss-stub'],  
                'x-argus': sg["x-argus"],  
                'x-gorgon': sg["x-gorgon"],  
                'x-khronos': sg["x-khronos"],  
                'x-ladon': sg["x-ladon"],  
            })  
            headers["accept-encoding"] = "identity"  
            response = requests.get(url, headers=headers, params=params)  

            try:  
                json_data = response.json()  
                if json_data.get('status_code') != 0:  
                    print("الكود يحتاج تجديد (قد يكون بسبب انتهاء صلاحية الكوكيز أو التوقيع)") 
                streamed_content = ""  
                for line in response.iter_lines():  
                    if line:  
                        decoded_line = line.decode('utf-8')  
                        if decoded_line.startswith('data: '):  
                            json_part = decoded_line[6:]  
                            try:  
                                data_part = json.loads(json_part)  
                                if 'choices' in data_part and len(data_part['choices']) > 0:  
                                    delta = data_part['choices'][0].get('delta', {})  
                                    if 'content' in delta and delta['content']:  
                                        streamed_content += delta['content']  
                            except json.JSONDecodeError:  
                                continue  
                if streamed_content:  
                    print(f"محتوى متدفق: {streamed_content}")  

                return json_data, response  
            except json.JSONDecodeError:  
                return False
                return None, response  
            except Exception as e:  
                #print(f"حدث خطأ أثناء معالجة الاستجابة: {e}")  
                return False, response  

        except Exception as e:  
            return e
import aiohttp
import asyncio
import re
from urllib.parse import urlparse, parse_qs, quote

class Gmail:
    async def CheckEmail(self, email):
        try:
            # Create session and use context manager to ensure proper cleanup
            async with aiohttp.ClientSession() as session:
                headers = {
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Connection': 'keep-alive',
                    'Host': 'accounts.google.com',
                    'sec-ch-ua': '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
                    'sec-ch-ua-arch': '"x86"',
                    'sec-ch-ua-bitness': '"64"',
                    'sec-ch-ua-full-version': '"121.0.6167.161"',
                    'sec-ch-ua-full-version-list': '"Not A(Brand";v="99.0.0.0", "Google Chrome";v="121.0.6167.161", "Chromium";v="121.0.6167.161"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-model': '""',
                    'sec-ch-ua-platform': '"Windows"',
                    'sec-ch-ua-platform-version': '"15.0.0"',
                    'sec-ch-ua-wow64': '?0',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Sec-Fetch-User': '?1',
                    'Upgrade-Insecure-Requests': '1',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                    'X-Chrome-ID-Consistency-Request': 'version=1,client_id=77185425430.apps.googleusercontent.com,device_id=8f1f3932-1eb5-4090-9f2b-252e0ea14109,signin_mode=all_accounts,signout_mode=show_confirmation',
                    'X-Client-Data': 'CI+VywE='
                }

                async with session.get('https://accounts.google.com/servicelogin?hl=en-gb', headers=headers) as response:
                    response_url = str(response.url)
                    parsed_url = urlparse(response_url)
                    query_params = parse_qs(parsed_url.query)
                    ifkv = query_params.get('ifkv', [None])[0]
                    dsh = query_params.get('dsh', [None])[0]
                    ifkv = quote(ifkv) if ifkv else None
                    dsh = quote(dsh) if dsh else None
        
                signup_url = f'https://accounts.google.com/lifecycle/flows/signup?biz=false&dsh={dsh}&flowEntry=SignUp&flowName=GlifWebSignIn&hl=en-gb&ifkv={ifkv}&theme=glif'
                
                headers = {
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Connection': 'keep-alive',
                    'Host': 'accounts.google.com',
                    'Referer': 'https://accounts.google.com/',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'same-origin',
                    'Sec-Fetch-User': '?1',
                    'Upgrade-Insecure-Requests': '1',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                    'X-Chrome-ID-Consistency-Request': 'version=1,client_id=77185425430.apps.googleusercontent.com,device_id=8f1f3932-1eb5-4090-9f2b-252e0ea14109,signin_mode=all_accounts,signout_mode=show_confirmation',
                    'X-Client-Data': 'CI+VywE=',
                    'sec-ch-ua': '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
                    'sec-ch-ua-arch': '"x86"',
                    'sec-ch-ua-bitness': '"64"',
                    'sec-ch-ua-full-version': '"121.0.6167.161"',
                    'sec-ch-ua-full-version-list': '"Not A(Brand";v="99.0.0.0", "Google Chrome";v="121.0.6167.161", "Chromium";v="121.0.6167.161"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-model': '""',
                    'sec-ch-ua-platform': '"Windows"',
                    'sec-ch-ua-platform-version': '"15.0.0"',
                    'sec-ch-ua-wow64': '?0'
                }
                
                async with session.get(signup_url, headers=headers) as response:
                    response_text = await response.text()
                    response_url = str(response.url)
                    parsed_url = urlparse(response_url)
                    query_params = parse_qs(parsed_url.query)
                    TL = query_params.get('TL', [None])[0]
                    TL = quote(TL) if TL else None
                    
                    snlmoe_pattern = r'"SNlM0e":"([^"]+)"'
                    fdrfje_pattern = r'"FdrFJe":"([^"]+)"'
                    snlmoe_match = re.search(snlmoe_pattern, response_text)
                    fdrfje_match = re.search(fdrfje_pattern, response_text)
                    AT = quote(snlmoe_match.group(1)) if snlmoe_match else None
                    FdrFJe = quote(fdrfje_match.group(1)) if fdrfje_match else None
        
                post_url = f'https://accounts.google.com/lifecycle/_/AccountLifecyclePlatformSignupUi/data/batchexecute?rpcids=E815hb&source-path=%2Flifecycle%2Fsteps%2Fsignup%2Fname&f.sid={FdrFJe}&bl=boq_identity-account-creation-evolution-ui_20240208.02_p2&hl=en-gb&TL={TL}&_reqid=407217&rt=c'
                payload = f'f.req=%5B%5B%5B%22E815hb%22%2C%22%5B%5C%22Harold%5C%22%2C%5C%22%5C%22%2C0%2C%5Bnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2C1%2C0%2C1%2C%5C%22%5C%22%2Cnull%2Cnull%2C1%2C1%5D%2Cnull%2C%5B%5D%2C%5B%5D%2C1%5D%22%2Cnull%2C%22generic%22%5D%5D%5D&at={AT}&'
                
                headers = {
                    'Accept': '*/*',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Connection': 'keep-alive',
                    'Content-Length': str(len(payload)),
                    'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
                    'Host': 'accounts.google.com',
                    'Origin': 'https://accounts.google.com',
                    'Referer': 'https://accounts.google.com/',
                    'Sec-Fetch-Dest': 'empty',
                    'Sec-Fetch-Mode': 'cors',
                    'Sec-Fetch-Site': 'same-origin',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                    'X-Chrome-ID-Consistency-Request': 'version=1,client_id=77185425430.apps.googleusercontent.com,device_id=8f1f3932-1eb5-4090-9f2b-252e0ea14109,signin_mode=all_accounts,signout_mode=show_confirmation',
                    'X-Client-Data': 'CI+VywE=',
                    'X-Same-Domain': '1',
                    'sec-ch-ua': '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
                    'sec-ch-ua-arch': '"x86"',
                    'sec-ch-ua-bitness': '"64"',
                    'sec-ch-ua-full-version': '"121.0.6167.161"',
                    'sec-ch-ua-full-version-list': '"Not A(Brand";v="99.0.0.0", "Google Chrome";v="121.0.6167.161", "Chromium";v="121.0.6167.161"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-model': '""',
                    'sec-ch-ua-platform': '"Windows"',
                    'sec-ch-ua-platform-version': '"15.0.0"',
                    'sec-ch-ua-wow64': '?0',
                    'x-goog-ext-278367001-jspb': '["GlifWebSignIn"]',
                    'x-goog-ext-391502476-jspb': f'["{dsh}",null,null,"{ifkv}"]'
                }

                async with session.post(post_url, data=payload, headers=headers) as response:
                    pass
        
                url = f'https://accounts.google.com/lifecycle/steps/signup/birthdaygender?TL={TL}&dsh={dsh}&flowEntry=SignUp&flowName=GlifWebSignIn&hl=en-gb&ifkv={ifkv}&theme=glif'
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
                }
                
                async with session.get(url, headers=headers) as response:
                    response_text = await response.text()
                    fdrfje_match = re.search(fdrfje_pattern, response_text)
                    FdrFJe = quote(fdrfje_match.group(1)) if fdrfje_match else None
        
                url = f'https://accounts.google.com/lifecycle/_/AccountLifecyclePlatformSignupUi/data/batchexecute?rpcids=eOY7Bb&source-path=%2Flifecycle%2Fsteps%2Fsignup%2Fbirthdaygender&f.sid={FdrFJe}&bl=boq_identity-account-creation-evolution-ui_20240208.02_p2&hl=en-gb&TL={TL}&_reqid=309055&rt=c'
                headers = {
                    'Accept': '*/*',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Connection': 'keep-alive',
                    'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
                    'Host': 'accounts.google.com',
                    'Origin': 'https://accounts.google.com',
                    'Referer': 'https://accounts.google.com/',
                    'Sec-Fetch-Dest': 'empty',
                    'Sec-Fetch-Mode': 'cors',
                    'Sec-Fetch-Site': 'same-origin',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                    'X-Chrome-ID-Consistency-Request': 'version=1,client_id=77185425430.apps.googleusercontent.com,device_id=8f1f3932-1eb5-4090-9f2b-252e0ea14109,signin_mode=all_accounts,signout_mode=show_confirmation',
                    'X-Client-Data': 'CI+VywE=',
                    'X-Same-Domain': '1',
                    'sec-ch-ua': '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
                    'sec-ch-ua-arch': '"x86"',
                    'sec-ch-ua-bitness': '"64"',
                    'sec-ch-ua-full-version': '"121.0.6167.161"',
                    'sec-ch-ua-full-version-list': '"Not A(Brand";v="99.0.0.0", "Google Chrome";v="121.0.6167.161", "Chromium";v="121.0.6167.161"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-model': '""',
                    'sec-ch-ua-platform': '"Windows"',
                    'sec-ch-ua-platform-version': '"15.0.0"',
                    'sec-ch-ua-wow64': '?0',
                    'x-goog-ext-278367001-jspb': '["GlifWebSignIn"]',
                    'x-goog-ext-391502476-jspb': f'["{dsh}",null,null,"{ifkv}"]'
                }
                
                birthday_payload = f'f.req=%5B%5B%5B%22eOY7Bb%22%2C%22%5B%5B1999%2C1%2C1%5D%2C1%2Cnull%2C0%2C%5Bnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2C1%2C0%2C1%2C%5C%22%5C%22%2Cnull%2Cnull%2C1%2C1%5D%2C%5C%22%3CxQlqCVECAAajugZng7qNVnUOPnQYop30ADQBEArZ1B6j7w8Uv8giVqAgzuPVvIA2XDCvV1SmYCWASaCIaN8PL7ZcE3buFHd0Wa7wGtoCzQAAAKedAAAAA6cBB1YHryeM4mO77iPiuTzu3P7tMbdL8aOoP6hx_5pRchqJXEBIm1fCOBQfj_wWypx7HDCrvrWxkOc7t3z-kH2Z72p7gsozI2LTfe1E9yNNzBONDH6f6rYu-F0Bx1Yl6_yQqzSgswF0Bpq3dBdFRrlS20nAYxFWzW0-U_QX2YfZGwJbDbCqWGqgaaYIj6q8n3ojD6_DcuUVjimPpmEkcfJZXoLpl2VK7gDfkmRyBglNiZiFyAxof1Dzoc_f2gqhh6l-WD8x1RuVHEouAIg6gV2ngSLnKGaW5PY7Vzv8Bu7LVmxkb6QE_YpmdKGSIktksXwMm7HK09bQtzBtyxZ5aBExgh-7gSq894cn7-G3dnb7Zkym-QezMR2EDyCYmufBzKqSzKEYDPr9uK_dMpd7Cd6kXjxls7Z5tMv6DzzTfU1mdvfEbANJ_kTU-U180q2HMpwDxlEcO__xZh5KUyqA_c0qdh8-hAScHpiCFs4tikJTh5fHK4TcafiwNsl0sp31yRZbHKzufmONTy9hrGLIf_6NAJnpy5EXSZ0aa2igt2j3pIomKxrU6p9Z1ZooW_1sEHEUvdTR2ZNz8PMCOj95FJyUhhPVt_SSOlg0wramlRA7puZxPKoQ0fYDZU-_cs24b5RZn6a8KwOJwbaaPgoSHebaiu9mYwQoh_F67HRO1-BNZkk1aybHgFnMUjdiaxvphByJL-HahGLQ9ej5Ha_Ub89Swc6i-igN87Z195_xew3x7bzPc7FLIpeIX_46yRXKjd6ETC73AafieKrmQWgF0nc__oiTZvbtv3vIrBQ914-7TXRvBu1N6OX5athmRCVMq8TeFNo5n1npkUm642DaXBCouMPtehBbmDekebggN5wA9GC-sfTHUfTQXQrCEY8zgC3-0W8qGOU98dfnkpVykHsUbvcXaNj9wJJ5quzKS-W39V6-7EoV_Ve2qpBNvoeE8AHH7tTVbLOiIpwRCdIJdwfNxD494r-m1JEBR_HifaHqfh011fksqQeF4pM40PresxUnarYD40lrg76fRA_uAuNU-kQFfk4kehq37YWhY60S0uwdzBraauoKEGT5HMNeOGzGrS9aNrcLLlKetpvSAO3ype-7Gje-vZq7_CZ57p63pIOkh43fmjvNYbsMwGEyBXZaYXWyAHPEX8qERe5IcilFP0wlWJtXBot0ig-w35qUn_fLbrv38HjQtyAsnu9wUpPpBN3OUaUgUXoSR--BVs6fdDzMdLygFGmiH8gDUQfti2ObSbQEtS5oHe-gB00qQ2CFjxSHNFhTB1naRxq1W_wSAPnGpxub9dWGzuEZ0_lBWkYDomx9vaeDUUS3EXXAgL4WfdI49BLPCVwm5NkiaHRZ-iq9OxjfhOSDWDiC3jq9NqFMzUnjMfJzjq-tkQcpr3HeCxCx_kJdFr99P_s49u9aJRPKEAqFedmJuNW6ul0sj7gfglu2DiCU2o71A_fgb5AZ1pD0JuI5DdZ-KE3phiCVVBZV-u3Wjj1FKFJJSRMrSMff-c5vXy14lgq4wGdIPtjqGZFcFyRes8F0FDn2AyNIcpD4LpKKg3wU5W0tE2vWA4RRUskli96ccd7SK35x6lauduMLPHxONhpTkvEQ45lucAaAv0va80vtrtD55g9HAj0iTxKwj5TL7DFfJ-0WS-w1gliuZ6IPfd5267pdbkjrRpnIXi4eqmUKMab_Hlf9_ZukC3f1cIUpjer4SW8fMpK3wlZtqUNoFZPavILmAenAkY59Ejx4TnBKQGwUhTW_78JR5OTOgKeE6rMQ28YodODdjhLDbOsMP1NTJ3KAzN0VTKh0QKmGxi1EzrW64vGsKzYdCiVbGrVf_ru8eTa3_GlbFByuSgZe3r8SU6N3MG2NCeadgW5rqjkiJLXIk9aPB0uS2sVrRHWqvm1JnTxmLPSZk7lUpMteJ-RtgxCotAqnTfiDVqKD1ApIRCUIRo0kpatT_tLb5UM_Li8a-IVnn_peH2srAq1mDo6tLthA1T2Ypz-57FQPVD6PXL-BCj7CQX0mS4n75j6v7BhIxlrmLOydGV3gh7VKfEQkgqL_vXdSuHRF6bzSCGAgI7moFcmDFXt2QCWEqaZx33Nl50CJq0EdUwylxdia2m_64BqWXMmCQe6BIQj1c8dVMArmF9YAl8M8J9L1XbSOTGCncNBaoKk9q9kWqYKV8Yn-cX8qndjXOF5Ws3IjWry7Xza4gMj-7CaYf-ioVP37ZZrtI7YOrrgsJVM1OvHkF7sAx3y_GL3HoqqFAVP-pa0_Nxse20s6v1ghr7RGzzN2O_tBccNGr24gPaVHqILBKYm36icKP2OZ1fn-Tsaexk-eM768P4bdEOd08w_Vo8EkYg0GUkr82rEHg50_T1OZRznUnKgakKorx_IaJgMknKDRzxB8EzjciW8zd_sHRjttT7VchbsZqgPnDnJNF0D_iSjvPxJ3d8ZqXtDNPPwVNweL_Ah0APZS1O0fuXD_HfemzqiBZErHbgbGDXTkeFkxL-pQjFIrHlknW5phQ1D7pxKHFyTchdjaVHo0SPGpDNbyf-6cP92oSFSfJLEYnd-EkBiV7QyBVT5VlLwNxPHHXzObxNMM2d89T6OHLtxMd60RKBHzHb-fzcnc_WTS%5C%22%2C%5B%5D%5D%22%2Cnull%2C%22generic%22%5D%5D%5D&at={AT}&'
                
                async with session.post(url, data=birthday_payload, headers=headers) as response:
                    pass
        
                url = f'https://accounts.google.com/lifecycle/steps/signup/username?TL={TL}&dsh={dsh}&flowEntry=SignUp&flowName=GlifWebSignIn&hl=en-gb&ifkv={ifkv}&theme=glif'
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
                }
                
                async with session.get(url, headers=headers) as response:
                    response_text = await response.text()
                    fdrfje_match = re.search(fdrfje_pattern, response_text)
                    FdrFJe = quote(fdrfje_match.group(1)) if fdrfje_match else None
        
                url = f'https://accounts.google.com/lifecycle/_/AccountLifecyclePlatformSignupUi/data/batchexecute?rpcids=NHJMOd&source-path=%2Flifecycle%2Fsteps%2Fsignup%2Fusername&f.sid={FdrFJe}&bl=boq_identity-account-creation-evolution-ui_20240208.02_p2&hl=en-gb&TL={TL}&_reqid=209557&rt=c'
                headers = {
                    'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                    'x-goog-ext-391502476-jspb': f'["{dsh}",null,null,"{ifkv}"]'
                }
                
                email_payload = f'f.req=%5B%5B%5B%22NHJMOd%22%2C%22%5B%5C%22{email}%5C%22%2C1%2C0%2C1%2C%5Bnull%2Cnull%2Cnull%2Cnull%2C0%2C151712%5D%2C0%2C40%5D%22%2Cnull%2C%22generic%22%5D%5D%5D&at={AT}&'
                
                async with session.post(url, data=email_payload, headers=headers) as response:
                    response_text = await response.text()
                    if response.status == 200:
                        if 'steps/signup/password' in response_text:
                            result = {'status': 'Good', 'Dev': 'Mustafa', 'Telegram': '@D_B_HH'}
                        else:
                            result = {'status': 'Bad', 'Dev': 'Mustafa', 'Telegram': '@D_B_HH'}
                    else:
                        result = {'status': response.status, 'Dev': 'Mustafa', 'Telegram': '@D_B_HH'}
                    # 
                    return result

        except Exception as e:
            return f'Error: {str(e)}'
import requests
import re

class Facebook:
    def GetIDs(self):
        try:
            n = int(input("كم رابط تريد؟ "))
        except Exception:
            print("اكتب رقم بابا")
            return None

        urls = []
        for i in range(1, n + 1):
            u = input(f"link{i}: ").strip()
            urls.append(u)

        ids = []
        for urll in urls:
            if not urll:
                ids.append("ماكو")
                continue
            try:
                r = requests.get(urll, timeout=10).text
                match = re.search(r'"userID":"(\d+)"', r)
                if match:
                    ids.append(match.group(1))
                else:
                    return {'status':'Bad','IDs':'ماكو' , 'Dev': 'Mustafa', 'Telegram': '@D_B_HH'}
            except Exception as e:
                return {'status':'Good','Info': e, 'Dev': 'Mustafa', 'Telegram': '@D_B_HH'}

        ids_str = ",".join(ids)
        return {'status':'Good','IDs': ids_str, 'Dev': 'Mustafa', 'Telegram': '@D_B_HH'}


    def GetApps(self,cok):
	    try:
	     	
		    cookies = {}
		    session=requests.session()
		    for part in cok.split(';'):
		        if '=' in part:
		            key, val = part.strip().split('=', 1)
		            cookies[key] = val
		
		    headers = {
		        'user-agent': 'NokiaX2-01/5.0 (08.35) Profile/MIDP-2.1 Configuration/CLDC-1.1 Mozilla/5.0 (Linux; Android 9; SH-03J) AppleWebKit/937.36 (KHTML, like Gecko) Safari/420+'
		    }
		
		    active_html = session.get('https://m.facebook.com/settings/apps/tabbed/?tab=active', cookies=cookies, headers=headers).text
		    expired_html = session.get('https://m.facebook.com/settings/apps/tabbed/?tab=inactive', cookies=cookies, headers=headers).text
		
		    lines = []  
		    lines.append("activities:")
		    apps = re.findall(r'data-testid="app_info_text">([^<]+)</span>', active_html)
		    dates = re.findall(r'(?:تمت الإضافة في|Added on|Ditambahkan pada|Ajouté le|Dodano dnia)\s*([^<]+)</p>', active_html)
		    if apps:
		        for i, app in enumerate(apps):
		            date = dates[i].strip() if i < len(dates) else "غير معروف"
		            lines.append(f"{i+1}. {app.strip()} - {date}")
		    else:
		        lines.append("No active apps")
		
		    lines.append("\nexpires:")
		    apps2 = re.findall(r'data-testid="app_info_text">([^<]+)</span>', expired_html)
		    dates2 = re.findall(r'(?:Kedaluwarsa pada|انتهت الصلاحية في)\s*([^<]+)</p>', expired_html)
		    if apps2:
		        for i, app in enumerate(apps2):
		            date = dates2[i].strip() if i < len(dates2) else "غير معروف"
		            lines.append(f"{i+1}. {app.strip()} - {date}")
		    else:
		        lines.append("No expired apps")
		
		    return "\n Dev : Mustafa | Tele : @D_B_HH \n".join(lines)
	    except:
	    	return 'problem'
	    	pass
