# -*- coding: utf-8 -*-
# Copyright (c) 2025 yaqiang.sun.
# This source code is licensed under the license found in the LICENSE file
# in the root directory of this source tree.
#########################################################################
# Author: yaqiangsun
# Created Time: 2025/10/20 18:24:01
########################################################################

import os
import os
import sys
import numpy as np
import matplotlib.pyplot as plt  # 引入 matplotlib 绘图库
# 获取当前文件的绝对路径，向上两层就是项目根目录
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


from qubitclient import QubitNNScopeClient
from qubitclient import NNTaskName

from qubitclient.nnscope.utils.data_parser import load_npz_file
from qubitclient.nnscope.nnscope_api.curve.curve_type import CurveType
from qubitclient.nnscope.utils.data_convert import convert_spectrum_npy2npz,convert_spectrum_dict2npz


def send_npz_to_server(url, api_key,dir_path = "data/33137"):

    # get all file in dir
    file_names = os.listdir(dir_path)

    file_path_list = []
    for file_name in file_names:
        if file_name.endswith('.npy') or file_name.endswith('.npz'):
            file_path = os.path.join(dir_path, file_name)
            file_path_list.append(file_path)
    if len(file_path_list)==0:
        return

    client = QubitNNScopeClient(url=url,api_key=api_key)

    dict_list = []
    for file_path in file_path_list:
        content = load_npz_file(file_path)
        dict_list.append(content)

    #使用从文件路径加载后的对象，格式为np.ndarray，多个组合成list
    response = client.request(file_list=dict_list,task_type=NNTaskName.SPECTRUM2D,curve_type=CurveType.COSINE)
    # 从文件路径直接加载
    # response = client.request(file_list=file_path_list,task_type=NNTaskName.SPECTRUM2D,curve_type=CurveType.COSINE)
    results = client.get_result(response=response)
    plot_result_npz(results,dict_list,file_names)

    print(results)


def send_npy_to_server(url, api_key,file_path = "/home/sunyaqiang/work/QubitClient/tmp/npyfile/tmp0bf97fdf.py_1536.npy"):

    # dict_list, name_list = convert_spectrum_npy2npz(file_path)
    
    client = QubitNNScopeClient(url=url,api_key=api_key)
    
    # 1.使用从文件路径加载后的对象，格式为np.ndarray，多个组合成list
    import numpy as np
    data_ndarray = np.load(file_path, allow_pickle=True)
    # data_dict = data_ndarray.item() if isinstance(data_ndarray, np.ndarray) else data_ndarray
    response = client.request(file_list=[data_ndarray],task_type=NNTaskName.SPECTRUM2D,curve_type=CurveType.COSINE)
    # 2.从文件路径直接加载
    # response = client.request(file_list=[file_path],task_type=NNTaskName.SPECTRUM2D,curve_type=CurveType.COSINE)
    results = client.get_result(response=response)
    plot_result_npy(results,data_ndarray)

    print(results)


def plot_result_npz(results,dict_list,file_names):
    nums = len(results)
    row = (nums // 3) + 1 if nums % 3 != 0 else nums // 3
    col = min(nums, 3)

    fig = plt.figure(figsize=(5 * col, 4 * row))

    for index in range(nums):
        ax = fig.add_subplot(row, col, index + 1)

        result = results[index]
        # print(result["params_list"])
        # print(result["linepoints_list"])
        # print(result["confidence_list"])
        file_name = file_names[index]


        # 增加结果坐标映射
        # frequency = dict_list[index]["frequency"] # 750
        # bias = dict_list[index]["bias"] # 42
        # reflection_points_lst = []
        # for i in range(len(result["linepoints_list"])):
        #     reflection_points = client.convert_axis(result["linepoints_list"][i], bias,frequency)
        #     reflection_points_lst.append(reflection_points)
        # points_list = reflection_points_lst

        points_list = []
        for i in range(len(result["linepoints_list"])):
            points_list.append(result["linepoints_list"][i])

        # plt.figure(figsize=(10, 6))
        plt.pcolormesh(dict_list[index]["bias"], dict_list[index]["frequency"],  dict_list[index]["iq_avg"], shading='auto', cmap='viridis')
        plt.colorbar(label='IQ Average')  # 添加颜色条
        colors = plt.cm.rainbow(np.linspace(0, 1, len(result["linepoints_list"])))
        for i in range(len(points_list)):
            reflection_points = points_list[i]
            reflection_points = np.array(reflection_points)
            xy_x = reflection_points[:, 0]  # 提取 x 坐标
            xy_y = reflection_points[:, 1]  # 提取 y 坐标
            plt.scatter(xy_x, xy_y, color=colors[i], label=f'XY Points{i}-conf:{round(result["confidence_list"][i],2)}', s=5, alpha=0.1)  # 绘制散点图
        # 图形设置
        plt.title(f"File: {file_name}")
        plt.xlabel("Bias")
        plt.ylabel("Frequency (GHz)")
        plt.legend()
    fig.tight_layout()
    # plt.show()
    file_name_save = "result.png"
    save_path = "./tmp/client/"+file_name_save
    # save_path = f"./tmp/client/result_{file_name}.png"
    save_dir = os.path.dirname(save_path)
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    fig.savefig(save_path)


def plot_result_npy(results,data_ndarray):
    nums = len(results)
    row = (nums // 3) + 1 if nums % 3 != 0 else nums // 3
    col = min(nums, 3)

    fig = plt.figure(figsize=(5 * col, 4 * row))
    data_dict = data_ndarray.item() if isinstance(data_ndarray, np.ndarray) else data_ndarray
    data_dict = data_dict['image']
    data_dict = data_dict.item() if isinstance(data_dict, np.ndarray) else data_dict
    dict_list = []
    q_list = data_dict.keys()



    for idx, q_name in enumerate(q_list):
        npz_dict = {}
        image_q = data_dict[q_name]
        data = image_q[0]
        if data.ndim != 2:
            raise ValueError("数据格式无效，data不是二维数组")
        data = np.array(data)
        data = np.abs(data)

        npz_dict['bias'] = image_q[1]
        npz_dict['frequency'] = image_q[2]
        npz_dict['iq_avg'] = data
        npz_dict['name'] = q_name
        dict_list.append(npz_dict)

    for index in range(nums):
        ax = fig.add_subplot(row, col, index + 1)

        result = results[index]


        points_list = []
        for i in range(len(result["linepoints_list"])):
            points_list.append(result["linepoints_list"][i])

        # plt.figure(figsize=(10, 6))
        plt.pcolormesh(dict_list[index]["bias"], dict_list[index]["frequency"],  dict_list[index]["iq_avg"], shading='auto', cmap='viridis')
        plt.colorbar(label='IQ Average')  # 添加颜色条
        colors = plt.cm.rainbow(np.linspace(0, 1, len(result["linepoints_list"])))
        for i in range(len(points_list)):
            reflection_points = points_list[i]
            reflection_points = np.array(reflection_points)
            xy_x = reflection_points[:, 0]  # 提取 x 坐标
            xy_y = reflection_points[:, 1]  # 提取 y 坐标
            plt.scatter(xy_x, xy_y, color=colors[i], label=f'XY Points{i}-conf:{round(result["confidence_list"][i],2)}', s=5, alpha=0.1)  # 绘制散点图
        # 图形设置
        file_name = dict_list[index]["name"]
        plt.title(f"File: {file_name}")

        plt.xlabel("Bias")
        plt.ylabel("Frequency (GHz)")
        plt.legend()
    fig.tight_layout()
    # plt.show()
    file_name_save = "result.png"
    save_path = "./tmp/client/"+file_name_save
    # save_path = f"./tmp/client/result_{file_name}.png"
    save_dir = os.path.dirname(save_path)
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    fig.savefig(save_path)

def plot_result_npz_plotly(results, dict_list, file_names):
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    nums = len(results)
    rows = (nums // 3) + 1 if nums % 3 != 0 else nums // 3
    cols = min(nums, 3)

    # 创建子图
    fig = make_subplots(
        rows=rows, cols=cols,
        subplot_titles=[f"File: {name}" for name in file_names],
        vertical_spacing=0.05,
        horizontal_spacing=0.1,
        x_title="Bias",
        y_title="Frequency (GHz)"
    )

    # 遍历每个结果绘制子图
    for index in range(nums):
        row = (index // cols) + 1
        col = (index % cols) + 1

        result = results[index]
        data = dict_list[index]

        # 准备点数据
        points_list = []
        for i in range(len(result["linepoints_list"])):
            points_list.append(np.array(result["linepoints_list"][i]))

        # 添加热力图
        heatmap = go.Heatmap(
            z=data["iq_avg"],
            x=data["bias"],
            y=data["frequency"],
            colorscale="Viridis",
            colorbar=dict(
                title="IQ Average",
                thickness=10,
                len=0.7,
                yanchor="middle",
                y=0.5
            ),
            showscale=(index == 0)  # 只在第一个子图显示颜色条
        )
        fig.add_trace(heatmap, row=row, col=col)

        # 添加散点
        colors = np.linspace(0, 1, len(points_list))
        for i, points in enumerate(points_list):
            if len(points) == 0:
                continue
            xy_x = points[:, 0]
            xy_y = points[:, 1]
            scatter = go.Scatter(
                x=xy_x,
                y=xy_y,
                mode="markers",
                marker=dict(
                    color=colors[i],
                    colorscale="Rainbow",
                    size=5,
                    opacity=0.1,
                    showscale=False
                ),
                name=f'XY Points{i}-conf:{round(result["confidence_list"][i], 2)}',
                legendgroup=f"group{index}",
                showlegend=(row == 1 and col == 1)  # 只在第一个子图显示图例
            )
            fig.add_trace(scatter, row=row, col=col)

    # 更新布局
    fig.update_layout(
        height=500 * rows,
        width=600 * cols,
        margin=dict(r=60, t=60, b=60, l=60),
        legend=dict(
            font=dict(family="Courier", size=12, color="black"),
            borderwidth=1
        )
    )

    # 更新坐标轴设置
    fig.update_xaxes(
        title_text="Bias",
        title_font=dict(size=10),  # 缩小字体
        title_standoff=8  # 增加标题与坐标轴的距离（单位：像素）
    )
    fig.update_yaxes(
        title_text="Frequency (GHz)",
        title_font=dict(size=10),
        title_standoff=8
    )

    # 保存图片
    save_path = "./tmp/client/result.png"
    save_dir = os.path.dirname(save_path)
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    fig.write_image(save_path)




def plot_result_npy_plotly(results, data_ndarray):
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    nums = len(results)
    rows = (nums // 3) + 1 if nums % 3 != 0 else nums // 3
    cols = min(nums, 3)

    # 处理数据字典
    data_dict = data_ndarray.item() if isinstance(data_ndarray, np.ndarray) else data_ndarray
    data_dict = data_dict['image']
    data_dict = data_dict.item() if isinstance(data_dict, np.ndarray) else data_dict
    dict_list = []
    q_list = data_dict.keys()

    # 准备数据列表
    for idx, q_name in enumerate(q_list):
        npz_dict = {}
        image_q = data_dict[q_name]
        data = image_q[0]
        if data.ndim != 2:
            raise ValueError("数据格式无效，data不是二维数组")
        data = np.array(data)
        data = np.abs(data)

        npz_dict['bias'] = image_q[1]
        npz_dict['frequency'] = image_q[2]
        npz_dict['iq_avg'] = data
        npz_dict['name'] = q_name
        dict_list.append(npz_dict)

    # 创建子图
    fig = make_subplots(
        rows=rows, cols=cols,
        subplot_titles=[f"File: {dict_list[i]['name']}" for i in range(nums)],
        vertical_spacing=0.05,
        horizontal_spacing=0.1,
        x_title="Bias",
        y_title="Frequency (GHz)"
    )

    # 遍历每个结果绘制子图
    for index in range(nums):
        row = (index // cols) + 1
        col = (index % cols) + 1

        result = results[index]
        data = dict_list[index]

        # 准备点数据
        points_list = []
        for i in range(len(result["linepoints_list"])):
            points_list.append(np.array(result["linepoints_list"][i]))

        # 添加热力图
        heatmap = go.Heatmap(
            z=data["iq_avg"],
            x=data["bias"],
            y=data["frequency"],
            colorscale="Viridis",
            colorbar=dict(
                title="IQ Average",
                thickness=10,
                len=0.7,
                yanchor="middle",
                y=0.5
            ),
            showscale=(index == 0)  # 只在第一个子图显示颜色条
        )
        fig.add_trace(heatmap, row=row, col=col)

        # 添加散点
        colors = np.linspace(0, 1, len(points_list))
        for i, points in enumerate(points_list):
            if len(points) == 0:
                continue
            xy_x = points[:, 0]
            xy_y = points[:, 1]
            scatter = go.Scatter(
                x=xy_x,
                y=xy_y,
                mode="markers",
                marker=dict(
                    color=colors[i],
                    colorscale="Rainbow",
                    size=5,
                    opacity=0.1,
                    showscale=False
                ),
                name=f'XY Points{i}-conf:{round(result["confidence_list"][i], 2)}',
                legendgroup=f"group{index}",
                showlegend=(row == 1 and col == 1)  # 只在第一个子图显示图例
            )
            fig.add_trace(scatter, row=row, col=col)

    # 更新布局
    fig.update_layout(
        height=500 * rows,
        width=600 * cols,
        margin=dict(r=60, t=60, b=60, l=60),
        legend=dict(
            font=dict(family="Courier", size=12, color="black"),
            borderwidth=1
        )
    )

    # 更新坐标轴设置
    fig.update_xaxes(
        title_text="Bias",
        title_font=dict(size=10),  # 缩小字体
        title_standoff=8  # 增加标题与坐标轴的距离（单位：像素）
    )
    fig.update_yaxes(
        title_text="Frequency (GHz)",
        title_font=dict(size=10),
        title_standoff=8
    )

    # 保存图片
    save_path = "./tmp/client/result.png"
    save_dir = os.path.dirname(save_path)
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    fig.write_image(save_path)








def main():
    from config import API_URL, API_KEY

    # 1. npz file.
    # base_dir = "data/1829"
    # send_npz_to_server(API_URL, API_KEY, base_dir)
    # 2. npy file.
    file_path = "/home/sunyaqiang/work/QubitClient/tmp/npyfile/tmp0ffc025b.py_4905.npy"
    # file_path = "/home/sunyaqiang/work/QubitClient/tmp/online/None3.npy"
    send_npy_to_server(API_URL, API_KEY, file_path)



if __name__ == "__main__":
    main()