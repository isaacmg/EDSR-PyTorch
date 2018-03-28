import os

from data import common

import numpy as np
import scipy.misc as misc

import torch
import torch.utils.data as data

class SRData(data.Dataset):
    def __init__(self, args, train=True):
        self.args = args
        self.train = train
        self.split = 'train' if train else 'test'
        self.scale = args.scale
        self.idx_scale = 0

        self._set_filesystem(args.dir_data)

        def _load_bin():
            self.images_hr = np.load(self._name_hrbin())
            self.images_lr = [
                np.load(self._name_lrbin(s)) for s in self.scale]

        if args.ext == 'img':
            self.images_hr, self.images_lr = self._scan()
        elif args.ext.find('sep') >= 0:
            self.images_hr, self.images_lr = self._scan()
            if args.ext.find('reset') >= 0:
                print('Preparing seperated binary files')
                for v in self.images_hr:
                    img_hr = misc.imread(v)
                    name_sep = v.replace(self.ext, '.npy')
                    np.save(name_sep, img_hr)
                for si, s in enumerate(self.scale):
                    for v in self.images_lr[si]:
                        img_lr = misc.imread(v)
                        name_sep = v.replace(self.ext, '.npy')
                        np.save(name_sep, img_lr)

            self.images_hr = [
                v.replace(self.ext, '.npy') for v in self.images_hr
            ]
            self.images_lr = [
                [v.replace(self.ext, '.npy') for v in self.images_lr[i]]
                for i in range(len(self.scale))
            ]

        elif args.ext.find('bin') >= 0:
            try:
                if args.ext.find('reset') >= 0:
                    raise IOError
                print('Loading a binary file')
                _load_bin()
            except:
                print('Preparing a binary file')
                bin_path = os.path.join(self.apath, 'bin')
                if not os.path.isdir(bin_path):
                    os.mkdir(bin_path)

                list_hr, list_lr = self._scan()
                hr = [misc.imread(f) for f in list_hr]
                np.save(self._name_hrbin(), hr)
                del hr
                for si, s in enumerate(self.scale):
                    lr_scale = [misc.imread(f) for f in list_lr[si]]
                    np.save(self._name_lrbin(s), lr_scale)
                    del lr_scale
                _load_bin()
        else:
            print('Please define data type')

    def _scan(self):
        raise NotImplementedError

    def _set_filesystem(self, dir_data):
        raise NotImplementedError

    def _name_hrbin(self):
        raise NotImplementedError

    def _name_lrbin(self, scale):
        raise NotImplementedError

    def __getitem__(self, idx):
        img_lr, img_hr = self._load_file(idx)
        img_lr, img_hr = self._get_patch(img_lr, img_hr)
        img_lr, img_hr = common.set_channel(
            img_lr, img_hr, self.args.n_colors)

        return common.np2Tensor(img_lr, img_hr, self.args.rgb_range)

    def __len__(self):
        return len(self.images_hr)

    def _get_index(self, idx):
        return idx

    def _load_file(self, idx):
        idx = self._get_index(idx)
        img_lr = self.images_lr[self.idx_scale][idx]
        img_hr = self.images_hr[idx]
        if self.args.ext == 'img':
            img_lr = misc.imread(img_lr)
            img_hr = misc.imread(img_hr)
        elif self.args.ext.find('sep') >= 0:
            img_lr = np.load(img_lr)
            img_hr = np.load(img_hr)

        return img_lr, img_hr

    def _get_patch(self, img_lr, img_hr):
        patch_size = self.args.patch_size
        scale = self.scale[self.idx_scale]
        multi_scale = len(self.scale) > 1
        if self.train:
            img_lr, img_hr = common.get_patch(
                img_lr, img_hr, patch_size, scale, multi_scale=multi_scale)
            img_lr, img_hr = common.augment(img_lr, img_hr)
        else:
            ih = img_lr.shape[0]
            iw = img_lr.shape[1]
            img_hr = img_hr[0:ih * scale, 0:iw * scale]

        return img_lr, img_hr

    def set_scale(self, idx_scale):
        self.idx_scale = idx_scale

