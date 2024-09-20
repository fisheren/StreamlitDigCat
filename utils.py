import pickle


# 以下为使用GoogleDrive 进行读取文件的函数
# def get_total_excel(thermo_flag, photo_flag):
#     if not thermo_flag and not photo_flag:
#         total_pkl = os.path.join(".", "total_excel", "total.pkl")
#         if not os.path.exists(total_pkl):
#             download_folder_contents(dir_dict["total_excel"], os.path.dirname(total_pkl))
#         with open(total_pkl, 'rb') as file:
#             df_total = pickle.load(file)
#         return df_total
#     elif photo_flag:
#         total_pkl = os.path.join(".", "total_pickle_photocatalysis", "photo_excel.pkl")
#         if not os.path.exists(total_pkl):
#             download_folder_contents(dir_dict["total_pickle_photocatalysis"], os.path.dirname(total_pkl))
#         with open(total_pkl, 'rb') as file:
#             df_total = pickle.load(file)
#         return df_total
#     elif thermo_flag:
#         total_pkl = os.path.join(".", "total_pickle_thermocatalysis", "thermo_excel.pkl")
#         if not os.path.exists(total_pkl):
#             download_folder_contents(dir_dict["total_pickle_thermocatalysis"], os.path.dirname(total_pkl))
#         with open(total_pkl, 'rb') as file:
#             df_total = pickle.load(file)
#         return df_total


def get_total_excel(thermo_flag, photo_flag):
    if not thermo_flag and not photo_flag:
        total_pkl = "./total_excel/total.pkl"
        with open(total_pkl, 'rb') as file:
            df_total = pickle.load(file)
        return df_total
    elif photo_flag:
        total_pkl = "./total_pickle_photocatalysis/photo_excel.pkl"
        with open(total_pkl, 'rb') as file:
            df_total = pickle.load(file)
        return df_total
    elif thermo_flag:
        total_pkl = "./total_pickle_thermocatalysis/thermo_excel.pkl"
        with open(total_pkl, 'rb') as file:
            df_total = pickle.load(file)
        return df_total
