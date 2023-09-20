import os


class SampleIDHandler:
    def __init__(self, base_folder):
        self.base_folder = base_folder
        self.sample_ids = {}
        self.scan()

    def scan(self):
        self.sample_ids = {}

        for root, dirs, files in os.walk(self.base_folder):
            for dir_name in dirs:
                full_folder_path = os.path.join(root, dir_name)
                if root == self.base_folder:
                    self.sample_ids[dir_name] = {"path": full_folder_path, "sub_ids": {}}
                else:
                    sample_id = os.path.basename(root)
                    if sample_id in self.sample_ids:
                        self.sample_ids[sample_id]["sub_ids"][dir_name] = full_folder_path

    def get_all_sample_ids(self):
        return list(self.sample_ids.keys())

    def get_all_sub_sample_ids(self, sample_id):
        if sample_id in self.sample_ids:
            return list(self.sample_ids[sample_id]["sub_ids"].keys())
        return []

    def get_full_sample_folder(self, sample_id):
        return self.sample_ids.get(sample_id, {}).get("path", None)

    def get_full_sub_sample_folder(self, sample_id, sub_sample_id):
        if sample_id in self.sample_ids and sub_sample_id in self.sample_ids[sample_id]["sub_ids"]:
            return self.sample_ids[sample_id]["sub_ids"][sub_sample_id]
        return None

    def to_sample_id(self, folder_path):
        rel_path = os.path.relpath(folder_path, self.base_folder)
        
        if os.path.sep in rel_path:
            parts = rel_path.split(os.path.sep)
            if len(parts) == 2 and parts[0] in self.sample_ids:
                return f"{parts[0]}:{parts[1]}"
        else:
            for sample_id, sub_ids in self.sample_ids.items():
                if rel_path == sub_ids["path"]:
                    return [f"{sample_id}:{sub}" for sub in sub_ids["sub_ids"]]
                elif rel_path == sub_ids.get("path", None):
                    return sample_id
        
        return None

    def to_path(self, sample_id):
        if ":" in sample_id:
            sample_id, sub_id = sample_id.split(":")
            sub_path = self.get_full_sub_sample_folder(sample_id, sub_id)
            if sub_path:
                return os.path.join(self.base_folder, sub_path)
        else:
            sample_path = self.get_full_sample_folder(sample_id)
            if sample_path:
                return os.path.join(self.base_folder, sample_path)
        
        return None
