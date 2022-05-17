from configure import *
# from WindPy import *
from iFinDPy import THS_DS
from tools_funs import *
from tools_class import CTHSAccount
from skyrim.whiterun import CCalendar

report_date = sys.argv[1]
calendar = CCalendar(os.path.join(CALENDAR_DIR, "cne_calendar.csv"))
prev_date = calendar.get_next_date(report_date, t_shift=-1)

# load THS account
run_account = CTHSAccount(
    t_account_id="htzq12157",
    t_password="247260",
)
run_account.log_in()
run_account.inquire_and_display_quotes()

# initialize contract set
contract_set = set()

# update from position
for download_date in [prev_date, report_date]:
    pos_file = "position.{}.csv".format(download_date)
    pos_path = os.path.join(INPUT_DIR, download_date[0:4], download_date, pos_file)
    if not os.path.exists(pos_path):
        print("There is not any position info available for {}".format(download_date))
    else:
        pos_df = pd.read_csv(pos_path, encoding="gb18030")
        pos_df["wind_code"] = pos_df.apply(
            lambda z: convert_contract_format(z["代码"], z["市场代码"], EXCHANGE_ID_ENG), axis=1)
        contract_set = contract_set.union(set(pos_df["wind_code"]))

# update from trades in this date
# some intra day trades may not exist in either prev date or this date
traded_file = "traded.{}.csv".format(report_date)
traded_path = os.path.join(INPUT_DIR, report_date[0:4], report_date, traded_file)
if not os.path.exists(traded_path):
    print("There is not any trades info available for {}".format(download_date))
else:
    traded_df = pd.read_csv(traded_path, encoding="gb18030")
    traded_df["wind_code"] = traded_df.apply(
        lambda z: convert_contract_format(z["合约代码"], z["交易所名称"], EXCHANGE_ID_CHS), axis=1)
    contract_set = contract_set.union(set(traded_df["wind_code"]))

# download
if len(contract_set) == 0:
    aux_df = pd.DataFrame(columns=["settle", "oi", "margin_rate"])
else:
    contract_list = list(contract_set)
    # w.start()
    # data_settle = w.wsd(contract_list, "settle", report_date, report_date, "")
    # data_oi = w.wsd(contract_list, "oi", report_date, report_date, "")
    # data_margin_rate = w.wsd(contract_list, "margin", report_date, report_date, "")
    # aux_df = pd.DataFrame(
    #     {
    #         "settle": pd.Series(data=data_settle.Data[0], index=contract_list),
    #         "oi": pd.Series(data=data_oi.Data[0], index=contract_list),
    #         "margin_rate": pd.Series(data=data_margin_rate.Data[0], index=contract_list),
    #     }
    # )

    data_settle = THS_DS(contract_list, "ths_settle_future", "", "", report_date, report_date)
    data_oi = THS_DS(contract_list, "ths_open_interest_future", "", "", report_date, report_date)
    data_margin_rate = THS_DS(contract_list, "ths_contract_long_deposit_future", "", "", report_date, report_date)
    aux_df = pd.DataFrame(
        {
            "settle": data_settle.data.set_index("thscode")["ths_settle_future"],
            "oi": data_oi.data.set_index("thscode")["ths_open_interest_future"],
            "margin_rate": data_margin_rate.data.set_index("thscode")["ths_contract_long_deposit_future"],
        }
    )
    aux_df["margin_rate"] = aux_df["margin_rate"] / MARGIN_RATE_SCALE
    aux_df = aux_df.sort_index(ascending=True)
    print("| {1} | {0} | aux data downloaded |\n".format(report_date, dt.datetime.now()))

save_dir = os.path.join(INPUT_DIR, report_date[0:4], report_date)
check_and_mkdir(save_dir)
save_file = "settle_info.{}.csv".format(report_date)
save_path = os.path.join(save_dir, save_file)
aux_df.to_csv(save_path, index_label="wind_code", float_format="%.2f")

print(aux_df)

# download market index
idx_label = "NHCI.SL"
idx_data = THS_DS(idx_label, 'ths_open_price_index;ths_high_price_index;ths_low_index;ths_close_price_index;ths_chg_ratio_index',
                  ';;;;', 'block:history', prev_date, prev_date)
idx_df = idx_data.data.rename(mapper={
    "ths_open_price_index": "OPEN",
    "ths_high_price_index": "HIGH",
    "ths_low_index": "LOW",
    "ths_close_price_index": "CLOSE",
    "ths_chg_ratio_index": "PCT_CHG",
}, axis=1)
idx_df["trade_date"] = prev_date
idx_df = idx_df[["trade_date", "OPEN", "HIGH", "LOW", "CLOSE", "PCT_CHG"]].set_index("trade_date")
idx_file = "market_index.{}.csv".format(prev_date)
save_dir = os.path.join(INPUT_DIR, prev_date[0:4], prev_date)
idx_path = os.path.join(save_dir, idx_file)
idx_df.to_csv(idx_path, index_label="trade_date", float_format="%.6f")
print(idx_df)
