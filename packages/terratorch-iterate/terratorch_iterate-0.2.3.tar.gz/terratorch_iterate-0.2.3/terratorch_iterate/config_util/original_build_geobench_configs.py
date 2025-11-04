import yaml
import glob
import pandas as pd

# files = glob.glob('/opt/app-root/src/fm-geospatial/pf/terratorch/examples/confs/geobenchv2_detection/*/*.yaml')
files = glob.glob(
    "/Users/ltizzei/Projects/Orgs/IBM/terratorch/examples/confs/geobenchv2_detection/*/*.yaml"
)

files_df = pd.DataFrame({"file": files})

files_df["dataset"] = [x.split("/")[-1].split("_")[0] for x in files_df["file"].values]

files_df["model"] = [
    x.split("/")[-1].replace(y + "_", "").replace(".yaml", "")
    for x, y in zip(files_df["file"].values, files_df["dataset"].values)
]

files_df = files_df[files_df["dataset"].values != "M4SAR"]
files_df = files_df[files_df["model"].values != "resnet50_torchgeo"]

files_df = files_df.sort_values(["model", "dataset"])

models = files_df["model"].unique()


for model in models:
    tmp_df = files_df[files_df["model"].values == model]

    tasks = []

    for i in range(tmp_df.shape[0]):
        with open("geobenchv2_template.yaml", "r") as file:
            template = yaml.safe_load(file)

        task_template = template["tasks"][0]
        template["experiment_name"] = model + "_geobench2_detection"

        with open(tmp_df["file"].values[i], "r") as file:
            data = yaml.safe_load(file)

        template["defaults"]["terratorch_task"]["model_args"]["backbone"] = data[
            "model"
        ]["init_args"]["model_args"]["backbone"]
        task_template["name"] = tmp_df["dataset"].values[i]
        task_template["metric"] = (
            "val_map"
            if data["model"]["init_args"]["model_args"]["framework"] == "faster-rcnn"
            else "val_segm_map"
        )
        task_template["terratorch_task"] = data["model"]["init_args"]
        task_template["datamodule"] = data["data"]
        # task_template['datamodule']['dict_kwargs']['batch_size'] = 8 if model != 'prithvi_600M' else 4
        # task_template['datamodule']['dict_kwargs']['eval_batch_size'] = 8 if model != 'prithvi_600M' else 4
        task_template["datamodule"]["dict_kwargs"]["batch_size"] = (
            8 if model != "prithvi_600M" else 4
        )
        task_template["datamodule"]["dict_kwargs"]["eval_batch_size"] = (
            8 if model != "prithvi_600M" else 4
        )

        tasks.append(task_template)

    template["tasks"] = tasks

    with open("geobenchv2_" + model + ".yaml", "w") as file:
        yaml.dump(template, file)
