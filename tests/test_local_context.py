import os,json,glob,shutil,filecmp,uuid
import unittest
from pathlib import Path

from context import LocalContext, LocalSession

class TestLocalContext(unittest.TestCase):
    def setUp(self) :
        os.makedirs('loc', exist_ok = True)
        os.makedirs('loc/task0', exist_ok = True)
        os.makedirs('loc/task1', exist_ok = True)
        for ii in ['loc/task0', 'loc/task1']:
            with open(os.path.join(ii, 'test0'),'w') as fp:
                fp.write(str(uuid.uuid4()))
            with open(os.path.join(ii, 'test1'),'w') as fp:
                fp.write(str(uuid.uuid4()))
            with open(os.path.join(ii, 'test2'),'w') as fp:
                fp.write(str(uuid.uuid4()))
            os.makedirs(os.path.join(ii, 'dir0'), exist_ok = True)
        os.makedirs('rmt', exist_ok = True)

    def tearDown(self):
        shutil.rmtree('loc')
        shutil.rmtree('rmt')

    def test_upload_non_exist(self) :
        work_profile = LocalSession({'work_path':'rmt'})
        self.job  = LocalContext(work_profile, 'loc')
        tasks = ['task0', 'task1']
        # test uploading non-existing file
        with self.assertRaises(RuntimeError):
            self.job.upload(tasks, ['foo'])

    def test_upload(self) :
        work_profile = LocalSession({'work_path':'rmt'})
        self.job  = LocalContext(work_profile, 'loc')
        self.job1 = LocalContext(work_profile, 'loc', job_uuid = self.job.job_uuid)
        tasks = ['task0', 'task1']
        files = ['test0', 'test1']
        self.job.upload(tasks, files)
        for ii in tasks :
            for jj in files :
                locf = os.path.join('loc', ii, jj)
                rmtf = os.path.join('rmt', self.job.job_uuid, ii, jj)
                with open(locf) as fp:
                    locs = fp.read()
                with open(rmtf) as fp:
                    rmts = fp.read()
                self.assertEqual(locs, rmts)
        self.job.upload(tasks, ['dir0'])
        for ii in tasks :
            for jj in ['dir0'] :
                locf = os.path.join('loc', ii, jj)
                rmtf = os.path.join('rmt', self.job.job_uuid, ii, jj)
                self.assertEqual(os.path.realpath(locf),
                                 os.path.realpath(rmtf))
        self.job1.upload(tasks, files)
        for ii in tasks :
            for jj in files :
                locf = os.path.join('loc', ii, jj)
                rmtf = os.path.join('rmt', self.job.job_uuid, ii, jj)
                with open(locf) as fp:
                    locs = fp.read()
                with open(rmtf) as fp:
                    rmts = fp.read()
                self.assertEqual(locs, rmts)


    def test_download_non_exist(self):
        work_profile = LocalSession({'work_path':'rmt'})
        self.job  = LocalContext(work_profile, 'loc')
        tasks = ['task0', 'task1']
        # down load non-existing file
        with self.assertRaises(RuntimeError):
            self.job.download(tasks, ['foo'])        

    def test_download(self):        
        # upload files
        work_profile = LocalSession({'work_path':'rmt'})
        self.job  = LocalContext(work_profile, 'loc')
        tasks = ['task0', 'task1']
        self.job.upload(tasks, ['test0', 'dir0'])
        # generate extra donwload files
        record_uuid = []
        for ii in tasks :
            for jj in ['test4', 'test5'] :
                with open(os.path.join('rmt',self.job.job_uuid,ii,jj), 'w') as fp:
                    tmp = str(uuid.uuid4())
                    fp.write(tmp)
                    record_uuid.append(tmp)
        # generate extra donwload dirs and files
        for ii in tasks :
            for jj in ['dir1'] :
                os.makedirs(os.path.join('rmt',self.job.job_uuid,ii,jj), exist_ok=False)
                for kk in ['test6']:
                    with open(os.path.join('rmt',self.job.job_uuid,ii,jj,kk), 'w') as fp:
                        tmp = str(uuid.uuid4())
                        fp.write(tmp)
                        record_uuid.append(tmp)                        
        # donwload
        files = ['test0', 'dir0', 'test4', 'test5', 'dir1']
        self.job.download(tasks, files)
        # check dlded
        cc = 0
        for ii in tasks :
            for jj in ['test4', 'test5'] :
                with open(os.path.join('loc',ii,jj), 'r') as fp:
                    tmp = fp.read()
                    self.assertEqual(tmp, record_uuid[cc])
                    cc += 1
        for ii in tasks :
            for jj in ['dir1'] :
                for kk in ['test6']:
                    with open(os.path.join('loc',ii,jj,kk), 'r') as fp:
                        tmp = fp.read()
                        self.assertEqual(tmp, record_uuid[cc])
                        cc += 1
        # check links preserved
        for ii in tasks :
            for jj in ['test0'] :
                locf = os.path.join('loc', ii, jj)
                rmtf = os.path.join('rmt', self.job.job_uuid, ii, jj)
                self.assertEqual(os.path.realpath(locf),
                                 os.path.realpath(rmtf))
        for ii in tasks :
            for jj in ['dir0'] :
                for kk in ['test6'] :
                    locf = os.path.join('loc', ii, jj, kk)
                    rmtf = os.path.join('rmt', self.job.job_uuid, ii, jj, kk)
                    self.assertEqual(os.path.realpath(locf),
                                     os.path.realpath(rmtf))
                
    def test_block_call(self) :
        work_profile = LocalSession({'work_path':'rmt'})
        self.job  = LocalContext(work_profile, 'loc')
        tasks = ['task0', 'task1']
        files = ['test0', 'test1']
        self.job.upload(tasks, files)
        # ls
        code, stdin, stdout, stderr = self.job.block_call('ls')
        self.assertEqual(stdout.read().decode('utf-8'), 'task0\ntask1\n')
        self.assertEqual(stdout.readlines(), ['task0\n','task1\n'])
        self.assertEqual(code, 0)
        code, stdin, stdout, stderr = self.job.block_call('ls a')
        self.assertEqual(code, 2)
        self.assertEqual(stderr.read().decode('utf-8'), 'ls: cannot access a: No such file or directory\n')

    def test_block_checkcall(self) :
        work_profile = LocalSession({'work_path':'rmt'})
        self.job  = LocalContext(work_profile, 'loc')
        tasks = ['task0', 'task1']
        files = ['test0', 'test1']
        self.job.upload(tasks, files)
        # ls
        stdin, stdout, stderr = self.job.block_checkcall('ls')
        self.assertEqual(stdout.read().decode('utf-8'), 'task0\ntask1\n')
        self.assertEqual(stdout.readlines(), ['task0\n','task1\n'])
        with self.assertRaises(RuntimeError):
            stdin, stdout, stderr = self.job.block_checkcall('ls a')
            
    def test_file(self) :
        work_profile = LocalSession({'work_path':'rmt'})
        self.job = LocalContext(work_profile, 'loc')
        self.assertFalse(self.job.check_file_exists('aaa'))
        tmp = str(uuid.uuid4())
        self.job.write_file('aaa', tmp)
        self.assertTrue(self.job.check_file_exists('aaa'))
        tmp1 = self.job.read_file('aaa')
        self.assertEqual(tmp, tmp1)
        
