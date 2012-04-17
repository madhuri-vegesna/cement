"""Tests for cement.core.setup."""

import unittest
from nose.tools import eq_, raises
from cement2.core import foundation, exc, backend, config, extension, plugin
from cement2.core import log, output, handler, hook, arg, controller
from cement2 import test_helper as _t
       
class TestOutputHandler(output.CementOutputHandler):
    file_suffix = None
    
    class Meta:
        interface = output.IOutput
        label = 'test_output_handler'
        
    def _setup(self, config_obj):
        self.config = config_obj
        
    def render(self, data_dict, template=None):
        return None

def my_hook_one(app):
    return 1
    
def my_hook_two(app):
    return 2

def my_hook_three(app):
    return 3
                
class FoundationTestCase(unittest.TestCase):
    def setUp(self):
        self.app = _t.prep()
        
    @raises(SystemExit)
    def test_default(self):
        try:
            self.app.setup()
            self.app.run()
        except SystemExit as e:
            raise
    
    def test_passed_handlers(self):
        from cement2.lib import ext_configparser
        from cement2.lib import ext_logging
        from cement2.lib import ext_argparse
        from cement2.lib import ext_plugin
        from cement2.lib import ext_nulloutput
    
        app = _t.prep('test',
            config_handler=ext_configparser.ConfigParserConfigHandler,
            log_handler=ext_logging.LoggingLogHandler(),
            arg_handler=ext_argparse.ArgParseArgumentHandler(),
            extension_handler=extension.CementExtensionHandler(),
            plugin_handler=ext_plugin.CementPluginHandler(),
            output_handler=ext_nulloutput.NullOutputHandler(),
            argv=[__file__, '--debug']
            )
        app.setup()

    def test_null_out(self):
        null = foundation.NullOut()
        null.write('nonsense')

    def test_render(self):
        # Render with default
        self.app.setup()
        self.app.render(dict(foo='bar'))

        # Render with no output_handler... this is hackish, but there are 
        # circumstances where app.output would be None.
        app = _t.prep('test', output_handler=None)
        app.setup()
        app.output = None
        app.render(dict(foo='bar'))

    @raises(exc.CementRuntimeError)
    def test_bad_label(self):
        try:
            app = foundation.CementApp(None)
        except exc.CementRuntimeError as e:
            # FIX ME: verify error msg
            raise
            
    def test_add_arg_shortcut(self):
        self.app.setup()
        self.app.add_arg('--foo', action='store')
    
    def test_reset_output_handler(self):
        app = _t.prep('test', argv=[], output_handler=TestOutputHandler)
        app.setup()
        app.run()
    
        app.output = None
    
        app._meta.output_handler = None
        app._setup_output_handler()

    @raises(NotImplementedError)
    def test_controller_handler(self):
        app = _t.prep('test',
            base_controller=controller.CementBaseController,
            argv=['default'],
            )
        handler.register(controller.CementBaseController)
        app.setup()
        try:
            app.run()
        except NotImplementedError as e:
            raise

    def test_lay_cement(self):
        app = _t.prep('test', argv=['--quiet'])
        app = _t.prep('test', argv=['--json', '--yaml'])
        
    def test_framework_hooks(self):
        hook_tuple = (0, my_hook_one.__name__, my_hook_one)    
        hook_tuple_two = (99, my_hook_two.__name__, my_hook_two)    
        hook_tuple_three = (-99, my_hook_three.__name__, my_hook_three)    
        backend.hooks['cement_pre_setup_hook'].append(hook_tuple)
        backend.hooks['cement_pre_setup_hook'].append(hook_tuple_two)
        backend.hooks['cement_pre_setup_hook'].append(hook_tuple_three)
        backend.hooks['cement_post_setup_hook'].append(hook_tuple)
        backend.hooks['cement_pre_run_hook'].append(hook_tuple)
        backend.hooks['cement_post_run_hook'].append(hook_tuple)
        self.app.setup()

        # check weight ordering
        eq_(backend.hooks['cement_pre_setup_hook'][0][1], 'my_hook_three')
        eq_(backend.hooks['cement_pre_setup_hook'][1][1], 'my_hook_one')
        eq_(backend.hooks['cement_pre_setup_hook'][2][1], 'my_hook_two')
    
    def test_none_member(self):
        class Test(object):
            var = None
    
        self.app.setup()    
        self.app.args.parsed_args = Test()
        try:
            self.app._parse_args()
        except SystemExit:
            pass
    
    @raises(exc.CementSignalError)
    def test_cement_signal_handler(self):
        import signal
        try:
            foundation.cement_signal_handler(signal.SIGTERM, 5)
        except exc.CementSignalError as e:
            eq_(e.signum, signal.SIGTERM)
            eq_(e.frame, 5)
            raise

    def test_cement_without_signals(self):
        app = _t.prep('test', catch_signals=None)
        app.setup()
    
    