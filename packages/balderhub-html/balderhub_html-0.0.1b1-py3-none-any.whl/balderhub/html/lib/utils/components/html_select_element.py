from balderhub.gui.lib.utils.mixins import SelectByVisibleTextMixin, SelectByIndexMixin, SelectByHiddenValueMixin

from . import HtmlOptionElement
from ..selector import Selector
from .html_element import HtmlElement


class HtmlSelectElement(HtmlElement, SelectByVisibleTextMixin, SelectByIndexMixin, SelectByHiddenValueMixin):
    """
    The element is implemented like described here: https://developer.mozilla.org/en-US/docs/Web/API/HTMLSelectElement
    """

    @property
    def options(self) -> list[HtmlOptionElement]:
        """
        :return: returns a list with all options of this select element
        """
        return [HtmlOptionElement(cur_bridge) for cur_bridge in self.bridge.find_bridges(Selector.by_tag("option"))]

    def _set_selected_option(self, option: HtmlOptionElement):
        """
        This method sets a given option as selected option.
        :param option: the option to set
        """
        if not option.is_selected():
            option.click()

    def select_by_text(self, visible_text: str):
        xpath = f".//option[text()='{visible_text}']"  # todo escape
        options = [HtmlOptionElement(cur_bridge) for cur_bridge in self.bridge.find_bridges(Selector.by_xpath(xpath))]
        if len(options) == 0 and " " in visible_text:
            filtered_options = [candidate for candidate in self.options if candidate.text == visible_text]
            if len(filtered_options) > 1:
                raise NotImplementedError('multiple options within selects is not supported yet')
            if len(filtered_options) == 1:
                self._set_selected_option(filtered_options[0])
                return
        elif len(options) > 1:
            # todo differ between single and multiple select
            raise NotImplementedError('multiple options within selects is not supported yet')
        else:
            self._set_selected_option(options[0])
            return
        raise ValueError(f'no option with visible text {visible_text}')

    def select_by_index(self, index: int):
        css = f"option[index='{str(index)}']"  # todo escape
        self._set_selected_option(
            HtmlOptionElement.by_selector(self.driver, Selector.by_css(css), parent=self)
        )
        options = [HtmlOptionElement(cur_bridge) for cur_bridge in self.bridge.find_bridges(Selector.by_css(css))]
        # todo differ between single and multiple select
        if len(options) == 0:
            raise ValueError(f'no option with index `{index}` in select `{self}`')
        if len(options) > 1:
            raise NotImplementedError('multiple options within selects is not supported yet')
        self._set_selected_option(options[0])

    def select_by_value(self, value: str) -> None:
        css = f"option[value='{value}']"  # todo escape
        options = [HtmlOptionElement(cur_bridge) for cur_bridge in self.bridge.find_bridges(Selector.by_css(css))]
        # todo differ between single and multiple select
        if len(options) == 0:
            raise ValueError(f'no option with value `{value}` in select `{self}`')
        if len(options) > 1:
            raise NotImplementedError('multiple options within selects is not supported yet')
        self._set_selected_option(options[0])
