import csv, os, json

import nibabel as nib
import numpy as np

from mmdps import BrainTemplate_old as BrainTemplate

class BrainNet:
	"""
	Currently there is only net constructors
	"""
	def __init__(self, net_config_file):
		self.net_config = json.load(open(net_config_file, 'r'))
		self.raw_data = None # raw .nii data
		self.net = None

	def generate_brain_net(self, raw_data_path, output_path):
		self.raw_data = nib.load(raw_data_path)
		for template_name in self.net_config['templates']:
			outfolder = os.path.join(output_path, template_name)
			os.makedirs(outfolder, exist_ok = True)
			self.gen_by_templatename(template_name, outfolder)

	def gen_by_templatename(self, template_name, outfolder):
		template = BrainTemplate.get_template(template_name)
		time_series = self.gen_timeseries_by_template(template)
		np.savetxt(os.path.join(outfolder, 'timeseries.csv'), time_series, delimiter=',')
		time_series_corr = np.corrcoef(time_series)
		self.net = time_series_corr
		np.savetxt(os.path.join(outfolder, 'corrcoef.csv'), time_series_corr, delimiter=',')

	def gen_timeseries_by_template(self, template):
		template_img = nib.load(template.niipath)
		self.set_positive_affine_x(self.raw_data)
		self.set_positive_affine_x(template_img)
		data = self.raw_data.get_data()
		template_data = template_img.get_data()
		timepoints = data.shape[3]
		timeseries = np.empty((template.count, timepoints))
		for i, region in enumerate(template.regions):
			regiondots = data[template_data == region, :]
			regionts = np.mean(regiondots, axis=0)
			timeseries[i, :] = regionts
		return timeseries

	def set_positive_affine_x(self, img):
		if img.affine[0, 0] < 0:
			aff = img.affine.copy()
			aff[0, 0] = -aff[0, 0]
			aff[0, 3] = -aff[0, 3]
			img.set_sform(aff)
			img.set_qform(aff)
			data = img.get_data()
			np.copyto(data, nib.flip_axis(data, axis=0))

class NodeFile:
	def __init__(self, initnode=None):
		nodedata = []
		if initnode:
			with open(initnode, newline='') as f:
				csvcontent = csv.reader(f, delimiter='\t')
				for row in csvcontent:
					nodedata.append(row)
		self.origin_nodedata = nodedata
		self.nodedata = nodedata.copy()
		self.count = len(nodedata)
	def reset(self):
		self.nodedata = self.origin_nodedata.copy()
	def write_node_file(self, fnamenode):
		with open(fnamenode, 'w', newline='') as f:
			writer = csv.writer(f, delimiter='\t')
			writer.writerows(self.nodedata)
	def change_column(self, col, colvalue):
		for irow in range(self.count):
			self.nodedata[irow][col] = colvalue[irow]
	def change_modular(self, modular):
		self.change_column(3, modular)
	def change_value(self, value):
		self.change_column(4, value)
	def change_label(self, label):
		self.change_column(5, label)
	def create_new_sub(self, subindexes):
		subnodefile = NodeFile()
		subnodefile.nodedata = sub_list(self.nodedata, subindexes)
		subnodefile.count = len(subindexes)
		return subnodefile

def sub_list(l, idx):
	nl = []
	for i in idx:
		nl.append(l[i])
	return nl

def get_nodefile(name):
	folder_module = os.path.dirname(os.path.abspath(__file__))
	folder_templates = os.path.join(folder_module, '../../../data/templates')
	folder_templates = os.path.abspath(folder_templates)
	nodepath = os.path.join(folder_templates, name)
	if os.path.isfile(nodepath):
		return NodeFile(nodepath)
	if os.path.isfile(name):
		return NodeFile(name)
	return NodeFile()

if __name__ == '__main__':
	nf = get_nodefile('brodmann_lr.node')
