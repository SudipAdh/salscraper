from selenium.webdriver import Chrome
from time               import sleep
from contextlib         import contextmanager

@contextmanager
def ctx_iframe(cdr, x_iframe):
    '''
        Executes the func on the given iframe
    '''
    if x_iframe :
        cdr.switch_to_frame(cdr.find_element_by_xpath(x_iframe))
    try:
        yield
    finally:
        if x_iframe :
            cdr.switch_to_default_content()

class CChrome(Chrome):
    def __init__(self):
        Chrome.__init__(self, executable_path='')

    def wait(self, xpath, x= 10):
        '''
            Waits for an element specified by xpath to be laoded.
        '''
        i = 1
        while True and i<=x:
            try :
                print('Waiting for {}, {}/{}'.format(xpath,i,x))
                i   += 1
                self.find_element_by_xpath(xpath)
                print('Found : {}'.format(xpath))
                return True
            except Exception as e:
                sleep(1)
        return False


    def scroll(self, xpath, s_time = 2):
        '''
            Scrollls to an element specified by xpath.
        '''
        self.execute_script('arguments[0].scrollIntoView(true);', self.find_element_by_xpath(xpath))
        sleep(s_time)

    def cclick(self, xpath):
        '''
            Clicks an element specified by xpath.
        '''
        self.scroll(xpath)
        self.find_element_by_xpath(xpath).click()

def A1(cdr, iccid= '89014103279036667344', imei= '866105034068130', zip= '90045'):
    try :
        url     = 'https://www.att.com/prepaid/activations/'

        x_iframe    = '//iframe[@id="lightbox_pop"]'
        x_close     = '//button[@id="mpel_elclose"]'
        x_iccid     = '//input[@id="simnumber"]'
        x_imei      = '//input[@id="imeinumber"]'
        x_zip       = '//input[@id="servicezip"]'
        x_cont      = '//button[@aria-disabled="false" and @id="continueBtn"]'
        x_assert    = '//p[contains(text(),"Select the type of device you want to activate")]'
        x_unfoc     = '//body[1]'


        cdr.get(url)

        if cdr.wait(x_iframe,5):
            with ctx_iframe(cdr, x_iframe):
                cdr.cclick(x_close)

        cdr.find_element_by_xpath(x_iccid).send_keys(iccid)
        cdr.find_element_by_xpath(x_imei).send_keys(imei)
        cdr.find_element_by_xpath(x_zip).send_keys(zip)


        cdr.cclick(x_unfoc)
        assert cdr.wait(x_cont,5)
        cdr.cclick(x_cont)

        assert cdr.wait(x_assert)
        return True
    except Exception as e:
        print(e)
        return False

def A2(cdr):
    try :
        x_select    = '//input[@id="deviceTypeDropDown"]'
        x_smrt      = '//li[@value="Smartphone"]'
        x_cont      = '//button[@aria-disabled="false" and @id="continueBtn"]'
        x_assert    = '//div[@id="emailDisclaimer"]'
        x_unfoc     = '//body[1]'

        assert cdr.wait(x_select,5)
        cdr.cclick(x_select)

        assert cdr.wait(x_smrt,5)
        cdr.cclick(x_smrt)

        cdr.cclick(x_unfoc)
        assert cdr.wait(x_cont,5)
        cdr.cclick(x_cont)

        assert cdr.wait(x_assert)
        return True
    except Exception as e:
        print(e)
        return False

def main():
    try :
        cdr     = CChrome()

        assert A1(cdr),'Failed at A1'
        print('A1 passed')
        assert A2(cdr),'Failed at A2'
        print('A2 passed')
        #assert A3(cdr),'Failed at A3'
        #print('A3 passed')

        #assert B1(cdr),'Failed at B1'
        #print('B1 passed')
        #assert B2(cdr),'Failed at B2'
        #print('B2 passed')
        #assert B3(cdr),'Failed at B3'
        #print('B3 passed')
    except Exception as e :
        print(e)
    finally :
        cdr.close()


if __name__ == '__main__':
    main()
