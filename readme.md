1、安装 subfinder
将 subfinder_2.6.6_linux_amd64.zip 上传到服务器，解压
unzip subfinder_2.6.6_linux_amd64.zip
sudo mv subfinder /usr/local/bin/
subfinder -v

2、安装相关插件
pip3 install -r requirements.txt

3、导入数据库
mysql -u root -p qiyelist < qiye_demo.sql
mysql -u root -p qiyelist < qiye_demo_domain_zichan.sql

4、上传企业列表压缩包并解压，如 panlong.zip
unzip panlong.zip

5、企业入库
python3 1\_处理企业名单入库.py -t panlong -p panlong

6、开始探测网络资产并入库
python3 2\_处理网络资产入库.py -t panlong -z panlong

# enterprise_net_asset
