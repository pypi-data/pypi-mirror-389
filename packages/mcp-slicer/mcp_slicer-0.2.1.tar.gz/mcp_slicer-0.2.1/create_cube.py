"""
在3D Slicer中创建立方体的脚本
在Slicer的Python Console中运行此脚本
"""

import slicer
import vtk

# 创建一个立方体源
cubeSource = vtk.vtkCubeSource()
cubeSource.SetXLength(50)
cubeSource.SetYLength(50)
cubeSource.SetZLength(50)
cubeSource.Update()

# 创建模型节点
cubeModelNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLModelNode")
cubeModelNode.SetName("Cube")

# 创建显示节点并设置颜色为绿色
cubeDisplayNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLModelDisplayNode")
cubeDisplayNode.SetColor(0.0, 1.0, 0.0)  # RGB: (0, 1, 0) - 绿色
cubeModelNode.SetAndObserveDisplayNodeID(cubeDisplayNode.GetID())

# 设置模型数据
cubeModelNode.SetAndObservePolyData(cubeSource.GetOutput())

print(f"立方体创建成功！")
print(f"名称: {cubeModelNode.GetName()}")
print(f"颜色: RGB(0, 1, 0) - 绿色")
print(f"尺寸: 50x50x50 mm")


