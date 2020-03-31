#!/usr/bin/python
import os
from os.path import expanduser
import fnmatch
import logging as log
import glob
import subprocess

import shutil
import ConfigParser
import psycopg2
import uuid
import tempfile
import re

from multiprocessing import Pool

SERVER_CONF = "server.conf"
DIR_CONFIG = os.path.dirname(os.path.realpath( __file__ ))
DIR_DIST = os.path.join(DIR_CONFIG,"enabled-addons/openerp")
DIR_DIST_ADDONS = os.path.join(DIR_DIST,"addons")
DIR_SERVER = os.path.abspath(os.path.join(DIR_CONFIG,".."))
DIR_WORKSPACE = os.path.abspath(os.path.join(DIR_SERVER,".."))

ADDON_META = "__openerp__.py"
ADDON_API = 8

ADDONS_IGNORED = []
ADDONS_INCLUDED = {
#       "addon-path" : [
#          "modulexy"
#        ]
}

def getDirs(inDir):
    res = []
    for dirName in os.listdir(inDir):
        if not dirName.startswith("."):
            if os.path.isdir(os.path.join(inDir,dirName)):
                res.append(dirName)

    return res


def listDir(inDir):
    res = []
    for item in os.listdir(inDir):
        if not item.startswith("."):
            res.append(item)
    return res


def getMaintainedModules():
    addonPattern = [
      os.path.join(DIR_SERVER,"addons-funkring*"),
      os.path.join(DIR_WORKSPACE,"addons-custom*")
    ]

    addons = []
    for curPattern in addonPattern:
        curDir = os.path.dirname(curPattern)
        for curAddonPackageDir in glob.glob(curPattern):
            curPackagePath = os.path.join(curDir,curAddonPackageDir)
            if os.path.isdir(curPackagePath):
                for curAddon in listDir(curPackagePath):
                    enabledPath = os.path.join(DIR_DIST_ADDONS,curAddon)
                    if os.path.exists(enabledPath):
                        addons.append(curAddon)

    return addons


def getCmd(args,opt=None):
    if opt.pipenv:
        log.info("Use pipenv")
        args = ["pipenv","run", "python2"] + args
    if not opt:
        return args
    if opt.db_host:
        args.append("--db_host")
        args.append(opt.db_host)
    if opt.db_port:
        args.append("--db_port")
        args.append(str(opt.db_port))
    if opt.db_password:
        args.append("--db_password")
        args.append(opt.db_password)
    if opt.db_user:
        args.append("--db_user")
        args.append(opt.db_user)
    if opt.test_enable:
        args.append("--test-enable")
    return args


def update(database=None, module=None, override=False, opt=None):
    if not database:
        return

    log.info("Update Database %s" % database)
    log.info("Update Modules: %s" % module)

    #translation export --module sale --lang de_DE --addons ${workspace_loc}/dist/addons --database openerp7_demo
    prog = os.path.join(DIR_SERVER,"run.py")
    cmdList = getCmd([str(prog),"update","--addons-path", str(DIR_DIST_ADDONS),"--database",database], opt)
    if opt:
      if opt.reinit:
        cmdList.append("--reinit")
        cmdList.append(opt.reinit)
    if module:
        cmdList.append("--module")
        cmdList.append(module)
    if override:
        cmdList.append("--override")
    subprocess.call(cmdList)


def console(database=None, opt=None):
    if not database:
        return
    prog = os.path.join(DIR_SERVER,"run.py")
    cmdList = getCmd(["-i",str(prog),"console","--addons-path", str(DIR_DIST_ADDONS),"--database",database], opt)
    subprocess.call(cmdList)

    
def po_export(database, opt):
    if not database:
        return

    log.info("Translation Export on Database %s" % database)
    log.info("Translation Export on Modules: %s" % opt.module)

    prog = os.path.join(DIR_SERVER,"run.py")
    cmdList = getCmd([str(prog),"po_export","--addons-path", str(DIR_DIST_ADDONS),"--database",database,"--module",opt.module], opt)
    if opt.lang:
      cmdList.append("--lang")
      cmdList.append(opt.lang)
    subprocess.call(cmdList)

    
def po_import(database, opt):
    if not database:
        return

    log.info("Translation Import on Database %s" % database)
    log.info("Translation Import on Modules: %s" % opt.module)

    prog = os.path.join(DIR_SERVER,"run.py")
    cmdList = getCmd([str(prog),"po_import","--addons-path", str(DIR_DIST_ADDONS),"--database",database,"--module",opt.module], opt)
    if opt.lang:
      cmdList.append("--lang")
      cmdList.append(opt.lang)
    subprocess.call(cmdList)


def unit_test(database, opt):
    if not database:
        return

    prog = os.path.join(DIR_SERVER,"run.py")
    cmdList = getCmd([str(prog),"test","--addons-path", str(DIR_DIST_ADDONS),"--database",database], opt)
    if opt.module:
      cmdList.append("--module")
      cmdList.append(opt.module)
    if opt.test_prefix:
      cmdList.append("--test-prefix")
      cmdList.append(opt.test_prefix)
    if opt.test_case:
      cmdList.append("--test-case")
      cmdList.append(opt.test_case)
    
    # check test directory
    cmdList.append("--test-download")
    if opt.test_download:
      testdir = opt.test_download     
    else:
      testdir = "~/.odoo-unit-test"
      
    testdir = expanduser(testdir)
    if not os.path.exists(testdir):
      os.mkdir(testdir)
    log.info("Test directory: %s" % testdir)
    cmdList.append(testdir)
    
    # call
    subprocess.call(cmdList)


def cleanup(database=None, fix=False, full=False, opt=None, delete_modules=None, delete_modules_full=None, delete_lower=False, delete_higher=False, only_models=False):
    if not database:
        return

    log.info("Cleanup Database %s" % database)

    prog = os.path.join(DIR_SERVER,"run.py")
    cmdList = getCmd([str(prog),"cleanup","--addons-path", str(DIR_DIST_ADDONS),"--database",database], opt)
    if fix:
        cmdList.append("--fix")
    if full:
        cmdList.append("--full")
    if delete_modules:
        cmdList.append("--delete")
        cmdList.append(delete_modules)
    if delete_modules_full:
        cmdList.append("--full-delete")
        cmdList.append(delete_modules_full)
    if delete_lower:
        cmdList.append("--delete-lower")
    if delete_higher:
        cmdList.append("--delete-higher")
    if only_models:
        cmdList.append("--only-models")
    subprocess.call(cmdList)


def findFile(directory, pattern):
    for root, dirs, files in os.walk(directory):
        for basename in files:
            if fnmatch.fnmatch(basename, pattern):
                filename = os.path.join(root, basename)
                yield filename


def cleanupPython(directory):
    for fileName in findFile(directory,"*.pyc"):
        os.remove(fileName)
        

def setup(onlyLinks=False):

    dirWorkspace = DIR_WORKSPACE
    dirEnabledAddons = DIR_DIST_ADDONS
    dirServer = DIR_SERVER
        
    dirFunkringAddons = os.path.join(dirServer,"addons-funkring")
    dirServerAddons = os.path.join(dirServer,"openerp/addons")
    dirAddons = os.path.join(dirWorkspace,"addons")

    #create path if not exists
    if not os.path.exists(dirEnabledAddons):
        os.makedirs(dirEnabledAddons)

    filesToCopy = [
        "openerp/addons/__init__.py"
    ]

    addonPattern = [
      dirFunkringAddons,
      dirServerAddons,
      dirAddons,      
      dirWorkspace+"/addons*",
      dirServer+"/addons*"
    ]

    ignoreAddons = ADDONS_IGNORED
    includeAddons = ADDONS_INCLUDED
    merged = []
    updateFailed = []
    
    if not onlyLinks:
      log.info("Cleanup all *.pyc Files")
      cleanupPython(dirWorkspace)

    if not os.path.exists(dirEnabledAddons):
        log.info("Create directory %s" % str(dirEnabledAddons))
        os.makedirs(dirEnabledAddons)

    t_removedLinks = 0
    t_addedLinks = 0

    dir_processed = set()
    dir_removed = set()
    dir_added = set()

    log.info("Delete current Symbolic links and distributed files " + str(dirEnabledAddons) + " ...")
    for curLink in glob.glob(dirEnabledAddons+'/*'):
        curLinkPath = os.path.join(dirEnabledAddons,curLink)
        #log.info("Found Link " + str(curLinkPath))
        is_link = os.path.islink(curLinkPath)
        if is_link: #or os.path.isfile(curLinkPath):
            #log.info("Remove link " + str(curLinkPath))
            os.remove(curLinkPath)
            if is_link:
                t_removedLinks+=1
                dir_removed.add(os.path.basename(curLink))

    log.info("Distribute Files " + str(dirEnabledAddons) + " ...")
    for fileToCopy in filesToCopy:
        fileToCopyPath = os.path.join(dirServer,fileToCopy)
        if os.path.exists(fileToCopyPath):
            fileDestPath = os.path.join(dirEnabledAddons,os.path.basename(fileToCopyPath))
            log.info("Copy File %s to %s " % (fileToCopyPath,fileDestPath))
            shutil.copyfile(fileToCopyPath, fileDestPath)

    #link per addon basis
    for curPattern in addonPattern:
        for curAddonPackageDir in glob.glob(curPattern):
            packageName = os.path.basename(curAddonPackageDir)
            if not curAddonPackageDir in dir_processed:
                dir_processed.add(curAddonPackageDir)
                log.info("process: " + curAddonPackageDir)
                if os.path.isdir(curAddonPackageDir):
                    #get include list
                    addonIncludeList = includeAddons.get(packageName,None)
                    #process addons
                    for curAddon in listDir(curAddonPackageDir):
                        if not curAddon in ignoreAddons and (addonIncludeList is None or curAddon in addonIncludeList):
                            curAddonPath = os.path.join(curAddonPackageDir, curAddon)
                            curAddonPathMeta = os.path.join(curAddonPath, ADDON_META)
                            if os.path.exists(curAddonPathMeta):
                                addonMeta = None
                                with open(curAddonPathMeta) as metaFp:
                                    addonMeta = eval(metaFp.read())
                                    
                                # check api
                                supported_api = addonMeta.get("api")
                                if not supported_api or ADDON_API in supported_api:                                     
                                    dstPath = os.path.join(dirEnabledAddons, curAddon)                            
                                    if not os.path.exists(dstPath) and not curAddonPath.endswith(".pyc"):
                                        #log.info("Create addon link " + str(dstPath) + " from " + str(curAddonPath))
                                        os.symlink(curAddonPath,dstPath)
                                        t_addedLinks += 1
                                        dir_added.add(curAddon)

            else:
                #log.info("processed twice: " + curAddonPackageDir)
                pass

    for cur_dir in dir_removed:
        if not cur_dir in dir_added:
            log.info("Removed Addin: " + cur_dir)

    for cur_dir in dir_added:
        if not cur_dir in dir_removed:
            log.info("Addin Added: " + cur_dir)

    if merged:
        log.info("\n\nMerged:\n * %s\n" % ("\n * ".join(merged),))

    if updateFailed:
        log.error("\n\nUnable to update:\n * %s\n" % ("\n * ".join(updateFailed),))

    log.info("Removed links: " + str(t_removedLinks))
    log.info("Added links: "  + str(t_addedLinks))
    log.info("Finished!")

def copyDatabase(database, dest):
    if not dest:
        log.info("No destination for copying the database to found!\n")
        
    log.info("Copy Database %s to %s " % (database, dest))
    
    tmpFile = tempfile.NamedTemporaryFile("w", bufsize=4096, suffix=".sql", prefix="pg_tmp_")
    try:
        # dump db
        p = subprocess.Popen(["pg_dump",database],stdout=tmpFile)
        p.wait()
        tmpFile.flush();

        # create db
        p = subprocess.Popen(["createdb", dest])
        p.wait()
        
        # import
        p = subprocess.Popen(["psql","-d", dest, "-f", tmpFile.name])
        p.wait()
    
        # update db
        con = psycopg2.connect("dbname=%s" % dest)
        database_uuid = str(uuid.uuid4())         
        try:
            cr = con.cursor()
            try:
                cr.execute("UPDATE ir_config_parameter SET value=%s WHERE key='database.uuid'", (database_uuid,))
                log.info("Changed Database UUID to %s" % database_uuid)
            finally:
                cr.close()
        finally:
            con.close()
    finally:
        tmpFile.close()


def getConnection(opt, db="postgres"):
    params = []
    params.append("dbname='%s'" % db)
    if opt.db_host:
        params.append("host='%s'" % opt.db_host)
    if opt.db_user:
        params.append("user='%s'" % opt.db_user)
    if opt.db_password:
        params.append("password='%s'" % opt.db_password)
    if opt.db_port:
        params.append("port='%s'" % opt.db_port)
    params = " ".join(params)
    return psycopg2.connect(params)


def getDatabases(name, opt):
    if "*" in name:        
        p = re.compile("^" + name.replace("*",".*") + "$") 
        con = getConnection(opt)
        try:
            cr = con.cursor()
            try:
                cr.execute("SELECT datname from pg_database")                
                return [r[0] for r in cr.fetchall() if p.match(r[0])]
            finally:
                cr.close()
        finally:
            con.close()
    else:
        return [name]


if __name__ == "__main__":
    import optparse

    log.basicConfig(level=log.INFO,
             format='%(asctime)s %(levelname)s %(message)s')
    
    # read basic server config if exists
    defaults = {}
    db_options = ["db_host","db_password","db_port","db_user"]
    if os.path.exists(SERVER_CONF):
        p = ConfigParser.ConfigParser()
        try:
            p.read([SERVER_CONF])
            for (name,value) in p.items('options'):
                if value and name in db_options:
                    if value.lower() == "none":
                        value = None
                    if value.lower() == "false":
                        value = False
                    if name == "db_port":
                        value = int(value)
                    if value:
                        defaults[name]=value              
        except IOError:
            pass
        except ConfigParser.NoSectionError:
            pass

    parser = optparse.OptionParser(description="Setup Util", usage="%prog [options]")
    parser.add_option("--links", dest="links", help="Ceate symbolic links", action="store_true", default=False)
    parser.add_option("--fix", dest="fix", help="Fix fixable automatically", action="store_true", default=False)
    parser.add_option("--full", dest="full", help="Enable full cleanup", action="store_true", default=False)
    parser.add_option("--update",dest="update",default=None,help="Update Database")
    parser.add_option("--po-export",dest="po_export",default=None,help="Export Translations")
    parser.add_option("--po-import",dest="po_import",default=None,help="Import Translations")
    parser.add_option("--lang",dest="lang",default=None,help="Language")
    parser.add_option("--console",dest="console",default=None,help="Start Console")
    parser.add_option("--copy",dest="copy",default=None,help="Copy Database")
    parser.add_option("--dest",dest="dest",default=None,help="Destination Database")
    parser.add_option("--threads",dest="threads",type="int",default=0,help="Threads for parallel processing")
    parser.add_option("--cleanup",dest="cleanup",default=None,help="Cleanup Database")
    parser.add_option("--module",dest="module",default=None,help="Module to Update")
    parser.add_option("--override",dest="override",action="store_true",default=False)
    parser.add_option("--db_host",dest="db_host",default=defaults.get("db_host"),help="Database Host")
    parser.add_option("--db_port",dest="db_port",default=defaults.get("db_port"),help="Database Port")
    parser.add_option("--db_password",dest="db_password",default=defaults.get("db_password"),help="Database Password")
    parser.add_option("--db_user",dest="db_user",default=defaults.get("db_user"),help="Database User")
    parser.add_option("--only-models",dest="only_models",action="store_true",help="Cleanup unused Models")
    parser.add_option("--list",dest="list",default=None, help="List Databases")
    parser.add_option("--full-delete", dest="full_delete_modules", help="Delete Modules with all data")
    parser.add_option("--delete", dest="delete_modules", help="Delete Modules only (data will be held)")
    parser.add_option("--delete-lower", action="store_true", help="Delete Lower Translation")
    parser.add_option("--delete-higher", action="store_true", help="Delete Higher Translation")
    parser.add_option("--reinit", dest="reinit", help="(Re)Init Views no or full")
    parser.add_option("--test-enable", action="store_true", help="Enable Test")
    parser.add_option("--test", dest="test", help="Run unit tests for database")
    parser.add_option("--test-prefix", dest="test_prefix", help="Only run tests which start with the passed prefix")
    parser.add_option("--test-case", dest="test_case", help="Only run test with the passed simple class name")
    parser.add_option("--test-download", dest="test_download", help="Add directory for test downloads (e.g. Reports)")
    parser.add_option("--pipenv", dest="pipenv", action="store_true", default=False, help="Start with pipenv")
    opt, args = parser.parse_args()

    # ####################################################################
    # DB FUNCTIONS
    # ####################################################################
    
    # function
    db_func = None
    databases = None
    
    # update
    def db_update(db):
        update(database=db, module=opt.module, override=opt.override, opt=opt)
        
    # cleanup
    def db_cleanup(db):
        cleanup(database=db, fix=opt.fix, full=opt.full, opt=opt, delete_modules=opt.delete_modules, 
                delete_modules_full=opt.full_delete_modules,
                delete_lower=opt.delete_lower,
                delete_higher=opt.delete_higher,
                only_models=opt.only_models)

    # test
    def db_test(db):
        unit_test(db, opt)
  
        
    # ####################################################################
    # Evaluate Parameters
    # ####################################################################

    if opt.links:
        setup(onlyLinks=True)
    elif opt.update:
        db_func = db_update
        databases = getDatabases(opt.update, opt)
    elif opt.test:
        db_func = db_test
        databases = getDatabases(opt.test, opt)
    elif opt.po_export:
        po_export(opt.po_export, opt)
    elif opt.po_import:
        po_import(opt.po_import, opt)
    elif opt.console:
        console(opt.console, opt)
    elif opt.cleanup:
        db_func = db_cleanup
        databases = getDatabases(opt.cleanup, opt)
    elif opt.copy:      
        copyDatabase(database=opt.copy, dest=opt.dest)   
    elif opt.list:
        for db in getDatabases(opt.list, opt):
            print db
    else:
        setup()
    
    
    # ####################################################################
    # EXECUTE DB FUNCTIONS
    # ####################################################################
 
    if db_func and databases:
        if not opt.threads:
            # single thread
            for db in databases:
                db_func(db)
        else:
            # multi thread
            log.info("Create thread pool for %s processes" % opt.threads)
            pool = Pool(processes=opt.threads)
            pool.map(db_func, databases)
        
        