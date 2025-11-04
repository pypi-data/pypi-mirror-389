from whisper_ai_zxs.whisper_tools import WhisperTools_UploadSellingProduct_Red, WhisperTools_UploadSellingProduct_Taobao
from whisper_ai_zxs.agent_servicer_TestStub import Agent_TestStub
from whisper_ai_zxs.whisper_tools import WhisperTools_Qywx

def test_analyze_red():
    tools1 = WhisperTools_UploadSellingProduct_Red("Manreya小红书店")
    tools1.analyze("/Users/lizhenhua/WeChatProjects/WhisperAI/tests/data/小红书商品库下载_Manreya小红书店.zip")
    tools2 = WhisperTools_UploadSellingProduct_Red("植想说小红书店")
    tools2.analyze("/Users/lizhenhua/WeChatProjects/WhisperAI/tests/data/小红书商品库下载_植想说小红书店.zip")

def test_analyze_taobao():
    tools1 = WhisperTools_UploadSellingProduct_Taobao("manreya旗")
    tools1.analyze("/Users/lizhenhua/WeChatProjects/WhisperAI/tests/data/淘宝在售商品_Manreya淘宝店/")
    tools2 = WhisperTools_UploadSellingProduct_Taobao("植想说天猫店")
    tools2.analyze("/Users/lizhenhua/WeChatProjects/WhisperAI/tests/data/淘宝在售商品_植想说天猫店/")

def test_WhisperTools_Qywx():
    agent = Agent_TestStub("植想说天猫店:亮亮")
    WhisperTools_Qywx.send_to_kf_robot_report(agent, 188, agent.get_shop_name(), "test", "更改地址", "this is a test!")

def test_cpca():
    import cpca
    cpca_result = cpca.transform(['江西省九江市柴桑区沙河街道沙河街镇 庐山东路中段柴玺欣园2栋2单元1506室【配送拨打:18465608371转2458】'])
    province = cpca_result.at[0, '省']
    city = cpca_result.at[0, '市']
    district = cpca_result.at[0, '区']
    address = cpca_result.at[0, '地址']
    print("省：",province)
    print("市：",city)
    print("区：",district)
    print("地址：",address)