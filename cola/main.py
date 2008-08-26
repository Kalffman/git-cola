# Copyright(C) 2008, David Aguilar <davvid@gmail.com>

import optparse
import sys
import os

from cola import utils
from cola import version
from cola.models import Model

def main():
    parser = optparse.OptionParser(
                        usage='%prog /repo/path-1 ... /repo/path-N*\n\n'
                              '*the current directory is used when no '
                              'paths are specified.')

    parser.add_option('-v', '--version',
                      help='Show cola version',
                      dest='version',
                      default=False,
                      action='store_true')

    parser.add_option('-s', '--style',
                      help='Applies a stylesheet',
                      dest='style',
                      metavar='STYLESHEET',
                      default='')

    opts, args = parser.parse_args()

    # This sets up sys.path so that the cola modules can be found.
    if opts.version or 'version' in args:
        print "cola version", version.version
        sys.exit(0)

    # allow "git cola /repo/path-1 .. /repo/path-N
    for repo in [ os.path.realpath(r) for r in args ]:
        if os.path.exists(repo):
            os.chdir(repo)
            utils.fork('git', 'cola')
        else:
            sys.stderr.write("cola: failed to open '%s': " +
                             "No such file or directory.\n" % r)
    # We launched cola so bail out
    if args:
        sys.exit(0)

    # load the model right away so that we can bail out when
    # no git repo exists
    model = Model()

    # PyQt4 -- defer this to allow git cola --version
    try:
        from PyQt4 import QtCore
        from PyQt4 import QtGui
    except ImportError:
        print >> sys.stderr, 'Sorry, you do not seem to have PyQt4 installed.'
        print >> sys.stderr, 'Please install it before using cola.'
        print >> sys.stderr, 'e.g.:    sudo apt-get install python-qt4'
        sys.exit(-1)

    class ColaApplication(QtGui.QApplication):
        """This makes translation work by throwing out the context."""
        wrapped = QtGui.QApplication.translate
        def translate(*args):
            trtxt = unicode(ColaApplication.wrapped('', *args[2:]))
            if trtxt[-6:-4] == '@@': # handle @@verb / @@noun
                trtxt = trtxt[:-6]
            return trtxt

    app = ColaApplication(sys.argv)
    QtGui.QApplication.translate = app.translate
    app.setWindowIcon(QtGui.QIcon(utils.get_icon('git.png')))
    locale = str(QtCore.QLocale().system().name())
    qmfile = utils.get_qm_for_locale(locale)
    if os.path.exists(qmfile):
        translator = QtCore.QTranslator(app)
        translator.load(qmfile)
        app.installTranslator(translator)

    # Add the images resource path for the stylesheets
    QtCore.QDir.setSearchPaths("images", [utils.get_image_dir()])
    if opts.style:
        # Allow absolute and relative paths to a stylesheet
        if os.path.isabs(opts.style) or os.path.exists(opts.style):
            filename = opts.style
        else:
            filename = utils.get_stylesheet(opts.style)
        if filename:
            stylesheet = open(filename, 'r')
            style = stylesheet.read()
            stylesheet.close()
            app.setStyleSheet(style)

    # simple mvc
    from cola.views import View
    from cola.controllers import Controller

    view = View(app.activeWindow())
    ctl = Controller(model, view)
    view.show()
    sys.exit(app.exec_())
