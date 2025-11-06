# 导入pandas库，用于数据处理和分析
import pandas as pd
# 从icetcore库导入相关模块
from icetcore import TCoreAPI, QuoteEvent, TradeEvent, BarType, GreeksType
# 导入os模块，用于操作系统相关功能（如文件路径操作）
import os

# 创建TCoreAPI实例，指定应用程序路径,使用时需要替换为客户端实际安装的路径
api = TCoreAPI(apppath="C:\AlgoMaster2\APPs64(DEV)")
# 建立API连接，空字符串表示使用默认连接参数
api.connect("")

# 获取历史合约信息 用来查找某一日有什么期权合约 symboltype="OPT"表示查询期权合约，dt="20251031"指定查询日期
all_symbol_his = api.getsymbolhistory(symboltype="OPT", dt="20251103")

# 参数设置
TARGET_UNDERLYING = '510050'  # 需要从查找结果提取的标的代码参数
TARGET_EXPIRY = '202511'  # 需要从查找结果提取的标的到期月份参数
satrttime = "2025110301"  # 获取历史数据的开始时间
endtime = "2025110416"  # 获取历史数据的结束时间
symbol_F = f"TC.F.U_SSE.{TARGET_UNDERLYING}.{TARGET_EXPIRY}" # 生成合成期货代码 用于查找Underlying Value的Close
# ===============================================1.提取某个商品全部合约代码===============================================================
symbol_list_call = []  # 创建空列表存储看涨期权合约代码
symbol_list_put = []   # 创建空列表存储看跌期权合约代码

# 递归遍历节点树查找目标标的和到期月份的合约
def traverse_nodes(node, target_underlying, target_expiry):
    calls = [] # 初始化
    puts = []  # 初始化
    # 检查当前节点是否包含子节点，因为all_symbol_his返回的是个嵌套的dict
    if 'Node' in node:
        # 遍历所有子节点
        for child in node['Node']:
            # 递归调用遍历函数，获取子节点的看涨和看跌期权列表
            c, p = traverse_nodes(child, target_underlying, target_expiry)
            # 将子节点的结果扩展到当前列表
            calls.extend(c)
            puts.extend(p)
    # 检查当前节点是否包含合约信息
    if 'Contracts' in node:
        # 检查是否是目标标的和到期月份
        for contract in node['Contracts']:
            # 将合约代码按点号分割成部分
            parts = contract.split('.')
            # 检查合约是否符合目标条件：包含足够部分、标的代码匹配、到期月份匹配
            if (len(parts) >= 6 and
                    parts[3] == target_underlying and
                    parts[4] == target_expiry):
                if parts[5] == 'C':
                    calls.append(contract)
                elif parts[5] == 'P':
                    puts.append(contract)

    return calls, puts

# 遍历整个数据结构查找目标合约
symbol_list_call, symbol_list_put = traverse_nodes(all_symbol_his, TARGET_UNDERLYING, TARGET_EXPIRY)

# 去重
symbol_list_call = list(set(symbol_list_call))
symbol_list_put = list(set(symbol_list_put))

print(symbol_list_call)
print(symbol_list_put)

# ===============================================2.将查找的合约代码循环带入获取历史数据并处理===============================================================
# 查找有没有指定目录没有的化创建输出目录processed_data
if not os.path.exists('processed_data'):
    os.makedirs('processed_data')

# 定义函数，从合约代码中提取行权价
def extract_strike_price(symbol):
    #将合约代码按.分割
    parts = symbol.split('.')
    # 检查是否有足够的部分（至少7部分）
    if len(parts) >= 7:
        # 如果部分数大于7，说明行权价包含小数点
        if len(parts) > 7:
            # 处理带小数点的行权价（如3.1）
            return float(f"{parts[6]}.{parts[7]}")
        else:
            return float(parts[6])
    return None

# 遍历处理每个合约的数据
for symbol in symbol_list_call + symbol_list_put:
    try:
        # 获取1分钟的历史数据
        df = pd.DataFrame(api.getquotehistory(BarType.MINUTE, 1, symbol, satrttime, endtime))
        # 检查数据框是否为空
        if not df.empty:
            # 移除时区信息
            if 'DateTime' in df.columns and hasattr(df['DateTime'].dtype, 'tz'):
                df['DateTime'] = df['DateTime'].dt.tz_localize(None)

            # 1. 把DateTime拆分为Date和Time
            df['Date'] = df['DateTime'].dt.date
            df['Time'] = df['DateTime'].dt.time

            # 2. 按照合约是C还是P，形成列Option Type
            option_type = 'C' if symbol in symbol_list_call else 'P'
            df['Option Type'] = option_type

            # 3. 截取合约行权价形成列Strike Price
            strike_price = extract_strike_price(symbol)
            df['Strike Price'] = strike_price

            # 4. 增加列LTP等于Close列
            if 'Close' in df.columns:
                df['LTP'] = df['Close']

            # 5. 查找每个合约的到期日和剩余交易日
            try:
                # 获取到期日
                expiry_date = api.getexpirationdate(symbol)
                df['Expiry'] = expiry_date

                # 获取剩余交易日
                # 从DateTime列提取日期和时间
                current_date = df['DateTime'].iloc[0].strftime('%Y%m%d')  # 格式化为20251105
                current_time_hour = df['DateTime'].iloc[0].strftime('%H')  # 提取小时数，如09

                trading_days = api.getexpirationex(2, symbol, current_date, current_time_hour)
                df['Time to Expiry'] = trading_days
            except Exception as e:
                print(f"获取{symbol}的到期信息失败: {str(e)}")
                df['Expiry'] = None
                df['Time to Expiry'] = None

            # 6. 按照指定顺序排列列
            required_columns = ['Symbol', 'Date', 'Time', 'Expiry', 'Option Type',
                                'Strike Price', 'Open', 'High', 'Low', 'Close',
                                'LTP', 'Time to Expiry']

            # 添加Symbol列
            df['Symbol'] = symbol

            # 只保留数据中存在的列
            available_columns = [col for col in required_columns if col in df.columns]
            df_final = df[available_columns]

            # 保存到文件
            filename = f"processed_data/{symbol.replace('.', '_')}.xlsx"
            df_final.to_excel(filename, index=False)
            print(f"已保存: {filename}")

    except Exception as e:
        print(f"处理合约 {symbol} 失败: {str(e)}")

print("所有合约数据处理完成！")

# ===============================================3. 按C/P分组合并合约数据===============================================================
# 导入glob模块，用于文件路径匹配
import glob

# 获取所有处理后的合约文件
processed_files = glob.glob('processed_data/*.xlsx')

# 创建空列表存储Call和Put数据
call_data = []
put_data = []

# 遍历所有处理后的文件
for file_path in processed_files:
    try:
        # 读取Excel文件
        df = pd.read_excel(file_path)
        if df.empty:
            continue

        # 从文件名判断合约类型
        filename = os.path.basename(file_path)
        if "_C_" in filename:
            call_data.append(df)
        elif "_P_" in filename:
            put_data.append(df)

    except Exception as e:
        print(f"读取文件失败 {file_path}: {e}")

# 合并Call合约数据
if call_data:
    call_combined = pd.concat(call_data, ignore_index=True)
    call_combined = call_combined.sort_values(['Date', 'Time'])
    call_combined.to_excel('call_contracts_combined.xlsx', index=False)

# 合并Put合约数据
if put_data:
    put_combined = pd.concat(put_data, ignore_index=True)
    put_combined = put_combined.sort_values(['Date', 'Time'])
    put_combined.to_excel('put_contracts_combined.xlsx', index=False)

print("数据合并完成")
# ===============================================4. 获取标的资产数据并合并到期权数据中===============================================================

# 获取合成期货数据，使用之前生成的合成期货代码
future_data = pd.DataFrame(api.getquotehistory(BarType.MINUTE, 1, symbol_F, satrttime, endtime))

# 处理数据
if not future_data.empty:
    # 移除时区信息
    if 'DateTime' in future_data.columns and hasattr(future_data['DateTime'].dtype, 'tz'):
        future_data['DateTime'] = future_data['DateTime'].dt.tz_localize(None)

    # 拆分DateTime为Date和Time
    future_data['Date'] = future_data['DateTime'].dt.date.astype(str)
    future_data['Time'] = future_data['DateTime'].dt.time.astype(str)

    # 重命名Close列为Underlying Value
    future_data['Underlying Value'] = future_data['Close']

    # 只保留需要的列
    future_data = future_data[['Date', 'Time', 'Underlying Value']]

# 读取Call合约合并数据并合并合成期货数据
if os.path.exists('call_contracts_combined.xlsx'):
    call_data = pd.read_excel('call_contracts_combined.xlsx')

    # 确保Date和Time列是字符串类型
    call_data['Date'] = call_data['Date'].astype(str)
    call_data['Time'] = call_data['Time'].astype(str)

    # 合并合成期货数据
    if not future_data.empty:
        call_data = pd.merge(call_data, future_data, on=['Date', 'Time'], how='left')

    # 按照行权价排序
    call_data = call_data.sort_values(['Date', 'Time', 'Strike Price'])

    # 保存合并后的数据
    call_data.to_excel('call_contracts_combined.xlsx', index=False)

# 读取Put合约合并数据并合并合成期货数据
if os.path.exists('put_contracts_combined.xlsx'):
    put_data = pd.read_excel('put_contracts_combined.xlsx')

    # 确保Date和Time列是字符串类型
    put_data['Date'] = put_data['Date'].astype(str)
    put_data['Time'] = put_data['Time'].astype(str)

    # 合并合成期货数据
    if not future_data.empty:
        put_data = pd.merge(put_data, future_data, on=['Date', 'Time'], how='left')

    # 按照行权价排序
    put_data = put_data.sort_values(['Date', 'Time', 'Strike Price'])

    # 保存合并后的数据
    put_data.to_excel('put_contracts_combined.xlsx', index=False)

print("标的资产数据合并完成")

# ===============================================5. Volatility Smile部分===============================================================

import matplotlib.pyplot as plt
import warnings
from py_vollib.black_scholes_merton.implied_volatility import implied_volatility
import os

warnings.filterwarnings('ignore')

# 使用处理好的call_contracts_combined或者put_contracts_combined文件，这里只用了call，用put就更换
sample_data = pd.read_excel('call_contracts_combined.xlsx')# 读取处理好的期权数据文件

# 确保数据按日期和时间排序，这是正确分组的前提
sample_data = sample_data.sort_values(['Date', 'Time'])

# 初始化IV列为0，用于存储隐含波动率
sample_data['IV'] = 0

# 直接对每一行数据计算隐含波动率
print(f"开始计算隐含波动率，共{len(sample_data)}个数据点...")

# 定义计算单行IV的函数
def calculate_iv(row):
    try:
        S = float(row['Underlying Value'])  # 标的资产价格
        K = float(row['Strike Price'])      # 行权价
        t = float(row['Time to Expiry']) / 243  # 年化时间（假设243个交易日）
        r = 0.0  # 无风险利率
        q = 0.0  # 股息率
        option_price = float(row['LTP'])  # 期权价格
        option_type = row['Option Type'].lower()  # 期权类型转为小写

        # 检查数据有效性
        if (pd.isna(S) or pd.isna(K) or pd.isna(t) or pd.isna(option_price) or
                t <= 0 or option_price <= 0 or S <= 0 or K <= 0):
            return 0.0

        # 使用py_vollib库计算隐含波动率
        iv = implied_volatility(option_price, S, K, t, r, q, option_type)
        return iv * 100

    except Exception as e:
        print(f"计算期权 {row['Symbol']} 的IV失败: {str(e)}")
        return 0.0001

# 使用apply函数直接对每一行计算IV
sample_data['IV'] = sample_data.apply(calculate_iv, axis=1)

print("隐含波动率计算完成！")
# 保存处理后的数据（包含IV列）
sample_data.to_excel('processed_data_with_iv.xlsx', index=False)

# 如果没有文件夹创建文件夹用来保存图片
if not os.path.exists('smile_plots'):
    os.makedirs('smile_plots')

# 定义绘制波动率微笑曲线的函数
def Plot_smile(date_val, time_val):
    # 筛选指定日期和时间的数据
    option_data = sample_data[
        (sample_data['Date'] == date_val) &
        (sample_data['Time'] == time_val)
        ]

    # 按行权价排序以确保曲线正确
    option_data = option_data.sort_values('Strike Price')

    plt.plot(option_data['Strike Price'], option_data['IV'])
    plt.legend([f"{date_val} {time_val}"])
    plt.ylabel('Implied Volatility')
    plt.xlabel('Strike Price')

    # 保存到文件夹
    filename = f"smile_plots/smile_{date_val}_{time_val}.png".replace(':', '').replace(' ', '_')
    plt.savefig(filename)
    plt.close()


# ===============================================6. Volatility Smile交易策略===============================================================

# 初始化信号、损益和市值标记列
sample_data['Signal'] = 0  # 交易信号：0=无持仓，1=有持仓
sample_data['PNL'] = 0     # 平仓损益
sample_data['MTM'] = 0     # 持仓损益

# 全局变量跟踪开仓位置
Open_position = None

# 获取数据总行数
total_rows = len(sample_data)

print(f"开始执行波动率微笑交易策略，共{total_rows}行数据...")

# 使用for循环遍历数据框的所有行，识别波动率微笑曲线中的异常凸起
# 逐行扫描同一时间点、相邻行权价的IV（隐含波动率）差异；
# 如果检测到"中间行权价的IV明显高于左右两边"（视为微笑曲线出现凸起bump），就建立蝶式套利组合：
# 卖出中间2口、买入左右各1口，等到凸起消失时平仓；
for row in range(1, total_rows - 1):# 从第1行到倒数第2行遍历
    # 检查当前没有持仓（Signal为0）
    if sample_data.iloc[row]['Signal'] == 0:
        # 判断期权状态：价内或价外
        ITM_check = sample_data.iloc[row]['Underlying Value'] > sample_data.iloc[row]['Strike Price']
        OTM_check = sample_data.iloc[row]['Underlying Value'] < sample_data.iloc[row]['Strike Price']
        # 检查前后行是否为同一时间点
        same_time_check_ahead = (sample_data.iloc[row]['Date'] == sample_data.iloc[row + 1]['Date'] and
                                 sample_data.iloc[row]['Time'] == sample_data.iloc[row + 1]['Time'])
        same_time_check_behind = (sample_data.iloc[row]['Date'] == sample_data.iloc[row - 1]['Date'] and
                                  sample_data.iloc[row]['Time'] == sample_data.iloc[row - 1]['Time'])

        # 第一种开仓条件：针对价内期权，且与前一行时间相同
        if ITM_check and same_time_check_behind:
            # 检查波动率微笑是否存在显著凸起：当前IV比前一个高1.5以上
            if sample_data.iloc[row]['IV'] > (sample_data.iloc[row - 1]['IV'] + 1.5):
                # 设置信号为1（开仓）
                sample_data.iloc[row, sample_data.columns.get_loc('Signal')] = 1
                # 计算开仓现金流：卖出2口中档期权，买入1口高档和1口低档期权
                sample_data.iloc[row, sample_data.columns.get_loc('PNL')] = (
                        2 * sample_data.iloc[row]['LTP'] -   # 卖出2口中档期权
                        sample_data.iloc[row + 1]['LTP'] -   # 买入1口高档期权
                        sample_data.iloc[row - 1]['LTP']     # 买入1口低档期权
                )

                # 记录开仓位置
                Open_position = row
                # 绘制开仓时的波动率微笑曲线
                Plot_smile(sample_data.iloc[row]['Date'], sample_data.iloc[row]['Time'])
                # 输出开仓信息
                if sample_data.iloc[row]['PNL'] > 0:
                    PnL = ["Money Received: INR", sample_data.iloc[row]['PNL']]
                elif sample_data.iloc[row]['PNL'] < 0:
                    PnL = ["Money Paid: INR", -sample_data.iloc[row]['PNL']]

                print("Position opened", "\nDate:", sample_data.iloc[row]['Date'],
                      "\nTime:", sample_data.iloc[row]['Time'],
                      "\nStrike Price:", sample_data.iloc[row]['Strike Price'],
                      "\n", PnL[0], PnL[1])

        # 第二种开仓条件：针对价外期权，且与后一行时间相同
        elif OTM_check and same_time_check_ahead:
            # 检查波动率微笑是否存在显著凸起：当前IV比后一个高1.5以上
            if sample_data.iloc[row]['IV'] > (sample_data.iloc[row + 1]['IV'] + 1.5):
                # 设置信号为1（开仓）
                sample_data.iloc[row, sample_data.columns.get_loc('Signal')] = 1
                # 计算开仓现金流：卖出2口中档期权，买入1口高档和1口低档期权
                sample_data.iloc[row, sample_data.columns.get_loc('PNL')] = (
                        2 * sample_data.iloc[row]['LTP'] -  # 卖出2口中档期权
                        sample_data.iloc[row + 1]['LTP'] -  # 买入1口高档期权
                        sample_data.iloc[row - 1]['LTP']    # 买入1口低档期权
                )

                # 记录开仓位置
                Open_position = row
                # 绘制开仓时的波动率微笑曲线
                Plot_smile(sample_data.iloc[row]['Date'], sample_data.iloc[row]['Time'])

                # 输出开仓信息
                if sample_data.iloc[row]['PNL'] > 0:
                    PnL = ["Money Received: INR", sample_data.iloc[row]['PNL']]  # 正值为收到权利金
                elif sample_data.iloc[row]['PNL'] < 0:
                    PnL = ["Money Paid: INR", -sample_data.iloc[row]['PNL']]    # 负值为支付权利金

                print("Position opened", "\nDate:", sample_data.iloc[row]['Date'],
                      "\nTime:", sample_data.iloc[row]['Time'],
                      "\nStrike Price:", sample_data.iloc[row]['Strike Price'],
                      "\n", PnL[0], PnL[1])

    # 平仓逻辑：当波动率微笑凸起消失时平仓
    # 检查是否存在未平仓部位，且当前行权价与开仓时一致
    elif (sample_data.iloc[row]['Signal'] == 1 and  # 当前有持仓
          Open_position is not None and             # 开仓位置存在
          sample_data.iloc[row]['Strike Price'] == sample_data.iloc[Open_position]['Strike Price']):

        # 价内期权平仓条件
        if sample_data.iloc[row]['Underlying Value'] > sample_data.iloc[row]['Strike Price']:

            # 检查前后行时间一致性
            same_time_check_behind = (sample_data.iloc[row]['Date'] == sample_data.iloc[row - 1]['Date'] and
                                      sample_data.iloc[row]['Time'] == sample_data.iloc[row - 1]['Time'])
            # 检查凸起是否消失：当前IV小于前一个IV
            if same_time_check_behind and sample_data.iloc[row]['IV'] < sample_data.iloc[row - 1]['IV']:

                # 设置信号为0（平仓）
                sample_data.iloc[row, sample_data.columns.get_loc('Signal')] = 0

                # 计算平仓现金流：反向操作，买入2口中档期权，卖出1口高档和1口低档期权
                sample_data.iloc[row, sample_data.columns.get_loc('PNL')] = (
                        -2 * sample_data.iloc[row]['LTP'] +    # 买入2口中档期权（平仓）
                        sample_data.iloc[row + 1]['LTP'] +     # 卖出1口高档期权（平仓）
                        sample_data.iloc[row - 1]['LTP']       # 卖出1口低档期权（平仓）
                )

                # 绘制平仓时的波动率微笑曲线
                Plot_smile(sample_data.iloc[row]['Date'], sample_data.iloc[row]['Time'])

                # 输出平仓信息
                if sample_data.iloc[row]['PNL'] > 0:
                    PnL = ["Money Received: INR", sample_data.iloc[row]['PNL']]   # 正值为平仓收入
                elif sample_data.iloc[row]['PNL'] < 0:
                    PnL = ["Money Paid: INR", -sample_data.iloc[row]['PNL']]      # 负值为平仓支出

                print("Position closed", "\nDate:", sample_data.iloc[row]['Date'],
                      "\nTime:", sample_data.iloc[row]['Time'],
                      "\nStrike Price:", sample_data.iloc[row]['Strike Price'],
                      "\n", PnL[0], PnL[1])

        # 价外期权平仓条件
        elif sample_data.iloc[row]['Underlying Value'] < sample_data.iloc[row]['Strike Price']:

            # 检查前后行时间一致性
            same_time_check_ahead = (sample_data.iloc[row]['Date'] == sample_data.iloc[row + 1]['Date'] and
                                     sample_data.iloc[row]['Time'] == sample_data.iloc[row + 1]['Time'])
            # 检查凸起是否消失：当前IV小于后一个IV
            if same_time_check_ahead and sample_data.iloc[row]['IV'] < sample_data.iloc[row + 1]['IV']:

                # 设置信号为0（平仓）
                sample_data.iloc[row, sample_data.columns.get_loc('Signal')] = 0

                # 计算平仓现金流：反向操作，买入2口中档期权，卖出1口高档和1口低档期权
                sample_data.iloc[row, sample_data.columns.get_loc('PNL')] = (
                        -2 * sample_data.iloc[row]['LTP'] +
                        sample_data.iloc[row + 1]['LTP'] +
                        sample_data.iloc[row - 1]['LTP']
                )

                # 绘制平仓时的波动率微笑曲线
                Plot_smile(sample_data.iloc[row]['Date'], sample_data.iloc[row]['Time'])

                # 输出平仓信息
                if sample_data.iloc[row]['PNL'] > 0:
                    PnL = ["Money Received: INR", sample_data.iloc[row]['PNL']]
                elif sample_data.iloc[row]['PNL'] < 0:
                    PnL = ["Money Paid: INR", -sample_data.iloc[row]['PNL']]

                print("Position closed", "\nDate:", sample_data.iloc[row]['Date'],
                      "\nTime:", sample_data.iloc[row]['Time'],
                      "\nStrike Price:", sample_data.iloc[row]['Strike Price'],
                      "\n", PnL[0], PnL[1])

        # 计算持仓的市值标记（MTM）
        if sample_data.iloc[row]['Signal'] == 1:

            # 检查前后行时间一致性
            same_time_check_ahead = (row < total_rows - 1 and
                                     sample_data.iloc[row]['Date'] == sample_data.iloc[row + 1]['Date'] and
                                     sample_data.iloc[row]['Time'] == sample_data.iloc[row + 1]['Time'])
            same_time_check_behind = (sample_data.iloc[row]['Date'] == sample_data.iloc[row - 1]['Date'] and
                                      sample_data.iloc[row]['Time'] == sample_data.iloc[row - 1]['Time'])
            # 如果前后行时间相同，计算当前持仓市值
            if same_time_check_ahead and same_time_check_behind:
                sample_data.iloc[row, sample_data.columns.get_loc('MTM')] = (
                        2 * sample_data.iloc[row]['LTP'] -
                        sample_data.iloc[row + 1]['LTP'] -
                        sample_data.iloc[row - 1]['LTP']
                )

    # 持仓状态传递：如果当前有持仓，将信号传递到下一行
    if sample_data.iloc[row]['Signal'] == 1 and row < total_rows - 1:
        sample_data.iloc[row + 1, sample_data.columns.get_loc('Signal')] = 1

# 计算累计损益：对PNL列进行累积求和
sample_data['Cumulative PNL'] = sample_data['PNL'].cumsum()

# 输出最终结果
if len(sample_data) > 0:
    print("\n\nCumulative PNL from volatility smile trading strategy: INR", sample_data.iloc[-1]['Cumulative PNL'])
else:
    print("\n\nNo data available for PNL calculation")

# 保存結果
sample_data.to_excel('volatility_smile_trading_results.xlsx', index=False)
print("波動率微笑交易策略執行完成，結果已保存！")


