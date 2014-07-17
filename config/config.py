#!/usr/bin/python
import os
import fnmatch
import logging as log
import glob
import subprocess

import shutil
import ConfigParser

SERVER_CONF = "server.conf"
DIR_CONFIG = os.path.dirname(os.path.realpath( __file__ ))
DIR_DIST = os.path.join(DIR_CONFIG,"enabled-addons/openerp")
DIR_DIST_ADDONS = os.path.join(DIR_DIST,"addons")
DIR_SERVER = os.path.abspath(os.path.join(DIR_CONFIG,".."))
DIR_WORKSPACE = os.path.abspath(os.path.join(DIR_SERVER,".."))

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
    return args

def getTranslations(database=None, modules=None, lang="de_DE", opt=None):
    if not modules:
        modules=",".join(getMaintainedModules())

    if not database:
        log.error("No Database passed")
        return

    prog = os.path.join(DIR_SERVER,"oe")
    cmdList = getCmd([str(prog),"translation","export","--addons", str(DIR_DIST_ADDONS),"--database",database,"--module",modules], opt)
    subprocess.call(cmdList)

def setTranslations(database=None, modules=None, lang="de_DE", opt=None):
    if not modules:
        modules=",".join(getMaintainedModules())

    if not database:
        log.error("No Database passed")
        return

    prog = os.path.join(DIR_SERVER,"oe")
    cmdList = getCmd([str(prog),"translation","import","--addons", str(DIR_DIST_ADDONS),"--database",database,"--module",modules], opt)
    subprocess.call(cmdList)


def update(database=None, module=None, override=False, opt=None):
    if not database:
        return

    log.info("Update Database %s" % database)
    log.info("Update Modules: %s" % module)

    #translation export --module sale --lang de_DE --addons ${workspace_loc}/dist/addons --database openerp7_demo
    prog = os.path.join(DIR_SERVER,"oe")
    cmdList = getCmd([str(prog),"update","--addons", str(DIR_DIST_ADDONS),"--database",database], opt)
    if module:
        cmdList.append("--module")
        cmdList.append(module)
    subprocess.call(cmdList)

def cleanup(database=None, fix=False, verbose=False, full=False, opt=None):
    if not database:
        return

    log.info("Cleanup Database %s" % database)

    prog = os.path.join(DIR_SERVER,"oe")
    cmdList = getCmd([str(prog),"cleanup","--addons", str(DIR_DIST_ADDONS),"--database",database], opt)
    if fix:
        cmdList.append("--fix")
    if verbose:
        cmdList.append("--verbose")
    if full:
        cmdList.append("--full")
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
                            curAddonPath = os.path.join(curAddonPackageDir,curAddon)
                            dstPath = os.path.join(dirEnabledAddons,curAddon)
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
    parser.add_option("--getTranslations",dest="getTranslations",help="Get Translations of a specified database",default=None)
    parser.add_option("--setTranslations",dest="setTranslations",help="Set Translations of a specified database",default=None)
    parser.add_option("--pushAll", dest="pushAll", help="Push all branches to Parent", action="store_true", default=False)
    parser.add_option("--commitAll",dest="commitAll",default=None,help="Commit All")
    parser.add_option("--links", dest="links", help="Ceate symbolic links", action="store_true", default=False)
    parser.add_option("--fix", dest="fix", help="Fix fixable automatically", action="store_true", default=False)
    parser.add_option("--full", dest="full", help="Enable full cleanup", action="store_true", default=False)
    parser.add_option("--verbose", dest="verbose", help="Verbose mode", action="store_true", default=False)
    parser.add_option("--update",dest="update",default=None,help="Update Database")
    parser.add_option("--cleanup",dest="cleanup",default=None,help="Cleanup Database")
    parser.add_option("--module",dest="module",default=None,help="Module to Update")
    parser.add_option("--override",dest="override",action="store_true",default=False)
    parser.add_option("--db_host",dest="db_host",default=defaults.get("db_host"),help="Database Host")
    parser.add_option("--db_port",dest="db_port",default=defaults.get("db_port"),help="Database Port")
    parser.add_option("--db_password",dest="db_password",default=defaults.get("db_password"),help="Database Password")
    parser.add_option("--db_user",dest="db_user",default=defaults.get("db_user"),help="Database User")
    opt, args = parser.parse_args()

    if opt.links:
        setup(onlyLinks=True)
    elif opt.getTranslations:
        getTranslations(database=opt.getTranslations, modules=opt.module, opt=opt)
    elif opt.setTranslations:
        setTranslations(database=opt.setTranslations, modules=opt.module, opt=opt)
    elif opt.update:
        update(database=opt.update, module=opt.module, override=opt.override, opt=opt)
    elif opt.cleanup:
        cleanup(database=opt.cleanup, fix=opt.fix, verbose=opt.verbose, full=opt.full, opt=opt)
    else:
        setup()