from vidata import ConfigManager
from napari.utils.colormaps import CyclicLabelColormap, DirectLabelColormap, label_colormap


if __name__ == "__main__":
    # cfg_file="/home/l727r/Desktop/Project_Utils/ViData/dataset_cfg/Cityscapes.yaml"
    # cm = ConfigManager(cfg_file)
    # print(cm)
    # print(cm.layers)
    # layer = cm.layer("Images")
    cm = label_colormap(num_colors=49, seed=0.5, background_value=0)
    print(cm.colors[0:5])
    print("\n")
    cm = label_colormap(num_colors=120, seed=0.5, background_value=0)
    print(cm.colors[0:5])
