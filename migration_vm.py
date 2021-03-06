#!/usr/bin/python
#encoding=utf-8
'''*******************************************************************************
# Author : Patrick Zheng
# Email : zzcahj@163.com
# Last modified : 2017-07-30 17:39
# Filename : migration_vm.py
#*******************************************************************************'''
import sys
import os
import uuid
import time
import subprocess

def migration_start(username,
                    password,
                    vcenter_ip,
                    datacenter_name,
                    resource_pool_name,
                    host_name,
                    vm_name,
                    migration_folder_name,
                    esxi_check):
    reload(sys)
    sys.setdefaultencoding(' utf-8 ')

    pid = os.fork()

    if pid>0:
        return
    else :
        log_file = open('./migration_log/%s_%s_%s.log'%(vcenter_ip,host_name,vm_name),
                        'w')
        log_file.close()
        record_log_file = open('./migration_log_file','a')
        record_log_file.write('./migration_log/%s_%s_%s.log\n'%(vcenter_ip,host_name,vm_name))
        record_log_file.close()
        os_pid = os.getpid()
        state_file = open('./migration_state','a')
        state = '{0: ^10}'.format('%s'%(os_pid)) + '|' + \
                '{0: ^18}'.format('%s'%(vcenter_ip)) + '|' + \
                '{0: ^18}'.format('%s'%(host_name)) + '|' + \
                '{0: ^12}'.format('%s'%(vm_name)) + '|' + \
                '{0: ^15}'.format('%s'%('未完成'))+'\n'
        state_file.write(state)
        state_file.close()
        username = username.replace('@','%40')
        datacenter_name = datacenter_name.replace(' ','%20')
        resource_pool_name = resource_pool_name.replace(' ','%20')
#begin vcenter migration
        if not esxi_check :
            vpx = 'vpx://%s@%s'%(username,vcenter_ip)
            if datacenter_name == '':
                if resource_pool_name == '' or resource_pool_name == host_name:
                    vpx = vpx + '/%s?no_verify=1'%(host_name)
                else:
                    vpx = vpx + '/%s/%s?no_verify=1'%(resource_pool_name,host_name)
            else:
                vpx = vpx + '/%s'%(datacenter_name)
                if resource_pool_name == '' or resource_pool_name == host_name:
                    vpx = vpx + '/%s?no_verify=1'%(host_name)
                else:
                    vpx = vpx + '/%s/%s?no_verify=1'%(resource_pool_name,host_name)
            get_return = \
            subprocess.Popen(['virt-v2v',
                              '-ic',
                              '%s'%(vpx),
                              '%s'%(vm_name),
                              '-o',
                              'local',
                              '-os',
                              '%s'%(migration_folder_name),
                              '-of',
                              'qcow2',
                              '--password-file',
                              '%s'%(password)],stdout=subprocess.PIPE)
            start_time = '开始时间: ' + time.strftime("%Y/%m/%d - %H:%M:%S")
            log_file = open('./migration_log/%s_%s_%s.log'%(vcenter_ip,host_name,vm_name),
                            'a')
            log_file.write(start_time+'\n')
            log_file.close()

            while True:
                out = get_return.stdout.readline()
                if 'Finishing off' in out:
                    get_state = os.popen('cat ./migration_state').readlines()
                    set_finish = []
                    for i in get_state:
                        if str(os_pid) in i:
                            i = i.replace('未完成','任务完成')
                        set_finish.append(i)
                    state_file = open('./migration_state','w')
                    for i in set_finish:
                        state_file.write(i)
                    state_file.close()
                    end_time = '结束时间: ' + time.strftime("%Y/%m/%d - %H:%M:%S")
                    log_file = open('./migration_log/%s_%s_%s.log'%(vcenter_ip,host_name,vm_name),
                                    'a')
                    log_file.write(start_time+'\n')
                    log_file.close()
                    os._exit(0)
                if out == '' and get_return.poll() != None:
                    get_state = os.popen('cat ./migration_state').readlines()
                    set_finish = []
                    for i in get_state:
                        if str(os_pid) in i:
                            i = i.replace('未完成','失败')
                        set_finish.append(i)
                    state_file = open('./migration_state','w')
                    for i in set_finish:
                        state_file.write(i)
                    state_file.close()
                    end_time = '结束时间: ' + time.strftime("%Y/%m/%d - %H:%M:%S")
                    log_file = open('./migration_log/%s_%s_%s.log'%(vcenter_ip,host_name,vm_name),
                                    'a')
                    log_file.write(start_time+'\n')
                    log_file.close()
                    os._exit(0)
                if 'Opening the overlay' in out:
                    log_file = open('./migration_log/%s_%s_%s.log'%(vcenter_ip,
                                                                    host_name,
                                                                    vm_name),
                                    'a')
                    log_file.write(out.rstrip('\n') + \
                                   ' 注意：长时间在这一步'+
                                   '没有更新下一步状态则'+
                                   '可能任务已经挂死，请检查目标虚拟机的快照是否已经整合\n')
                    log_file.close()
                    continue
                log_file = open('./migration_log/%s_%s_%s.log'%(vcenter_ip,
                                                                host_name,
                                                                vm_name),
                                'a')
                log_file.write(out)
                log_file.close()

#begin esxi migration
#begin copy to local first
        esxi = 'esx://%s@%s/?no_verify=1'%(username,vcenter_ip)
        os.system('mkdir ./%s -p'%(vm_name))
        os.chdir('./%s'%(vm_name))
        start_time = '开始时间: ' + time.strftime("%Y/%m/%d - %H:%M:%S")
        log_file = open('../migration_log/%s_%s_%s.log'%(vcenter_ip,host_name,vm_name),
                        'a')
        log_file.write(start_time+'\n')
        log_file.close()
        os.popen('nohup ' + \
                 'virt-v2v-copy-to-local ' +
                 '-ic %s %s --password-file %s > ../migration_log/%s_%s_%s.log'%(esxi,
                                                                                vm_name,
                                                                                password,
                                                                                vcenter_ip,
                                                                                host_name,
                                                                                vm_name))
        get_return = os.popen('cat ../migration_log/%s_%s_%s.log'%(vcenter_ip,
                                                                  host_name,
                                                                  vm_name)).read()
        if 'Finishing off' in get_return:
            get_state = os.popen('cat ../migration_state').readlines()
            set_finish = []
            for i in get_state:
                if str(os_pid) in i:
                    i = i.replace('未完成','开始转换')
                set_finish.append(i)
            state_file = open('../migration_state','w')
            for i in set_finish:
                state_file.write(i)
            state_file.close()
            end_time = '拷贝结束时间: ' + time.strftime("%Y/%m/%d - %H:%M:%S")
            log_file = open('../migration_log/%s_%s_%s.log'%(vcenter_ip,host_name,vm_name),
                'a')
            log_file.write(end_time+'\n')
            log_file.close()
        else:
            get_state = os.popen('cat ../migration_state').readlines()
            set_finish = []
            for i in get_state:
                if str(os_pid) in i:
                    i = i.replace('未完成','失败')
                set_finish.append(i)
            state_file = open('../migration_state','w')
            for i in set_finish:
                state_file.write(i)
            state_file.close()
            end_time = '结束时间: ' + time.strftime("%Y/%m/%d - %H:%M:%S")
            log_file = open('../migration_log/%s_%s_%s.log'%(vcenter_ip,host_name,vm_name),
                            'a')
            log_file.write(end_time+'\n')
            log_file.close()
            os.chdir('../')
            os.system('rm %s -rf'%(vm_name))
            os._exit(0)
#begin convert
        os.environ['LIBGUESTFS_BACKEND'] = 'direct'
        vm_name_xml = '%s.xml'%(vm_name)
        get_return = \
            subprocess.Popen(['virt-v2v',
                              '-i',
                              'libvirtxml',
                              '%s'%(vm_name_xml),
                              '-o',
                              'local',
                              '-os',
                              '%s'%(migration_folder_name),
                              '-of',
                              'raw'],stdout=subprocess.PIPE)
        start_time = '开始时间: ' + time.strftime("%Y/%m/%d - %H:%M:%S")
        log_file = open('../migration_log/%s_%s_%s.log'%(vcenter_ip,host_name,vm_name),
                        'a')
        log_file.write(start_time+'\n')
        log_file.close()
        while True:
            out = get_return.stdout.readline()
            if 'Finishing off' in out:
                get_state = os.popen('cat ../migration_state').readlines()
                set_finish = []
                for i in get_state:
                    if str(os_pid) in i:
                        i = i.replace('开始转换','任务完成')
                    set_finish.append(i)
                state_file = open('../migration_state','w')
                for i in set_finish:
                    state_file.write(i)
                state_file.close()
                end_time = '结束时间: ' + time.strftime("%Y/%m/%d - %H:%M:%S")
                log_file = open('../migration_log/%s_%s_%s.log'%(vcenter_ip,host_name,vm_name),
                                'a')
                log_file.write(end_time+'\n')
                log_file.close()
                os.chdir('../')
                os.system('rm %s -rf'%(vm_name))
                os._exit(0)
            if out == '' and get_return.poll() != None:
                get_state = os.popen('cat ../migration_state').readlines()
                set_finish = []
                for i in get_state:
                    if str(os_pid) in i:
                        i = i.replace('开始转换','失败')
                    set_finish.append(i)
                state_file = open('../migration_state','w')
                for i in set_finish:
                    state_file.write(i)
                state_file.close()
                end_time = '结束时间: ' + time.strftime("%Y/%m/%d - %H:%M:%S")
                log_file = open('../migration_log/%s_%s_%s.log'%(vcenter_ip,host_name,vm_name),
                                'a')
                log_file.write(end_time+'\n')
                log_file.close()
                os.chdir('../')
                os.system('rm %s -rf'%(vm_name))
                os._exit(0)
            if 'Opening the overlay' in out:
                log_file = open('../migration_log/%s_%s_%s.log'%(vcenter_ip,
                                                                host_name,
                                                                vm_name),
                                'a')
                log_file.write(out.rstrip('\n') + \
                               ' 注意：长时间在这一步'+
                               '没有更新下一步状态则'+
                               '可能任务已经挂死，请检查目标虚拟机的快照是否已经整合\n')
                log_file.close()
                continue
            log_file = open('../migration_log/%s_%s_%s.log'%(vcenter_ip,
                                                            host_name,
                                                            vm_name),
                            'a')
            log_file.write(out)
            log_file.close()
