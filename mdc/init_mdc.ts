/*
 * Copyright 2019-2025 Simon Zigelli
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import {MDCRipple} from '@material/ripple';
import {MDCTextField} from '@material/textfield';
import {MDCDataTable} from '@material/data-table';
import {MDCTopAppBar} from '@material/top-app-bar';
import {MDCMenu} from '@material/menu';

const buttonElements = [].slice.call(document.querySelectorAll('.mdc-button'));
buttonElements.forEach((buttonEl: Element) => {
    new MDCRipple(buttonEl);
});
const iconButtonElements = [].slice.call(document.querySelectorAll('.mdc-icon-button'));
iconButtonElements.forEach((iconButtonEl: Element) => {
    const iconButtonRipple = new MDCRipple(iconButtonEl);
    iconButtonRipple.unbounded = true;
});
const textFieldElements = [].slice.call(document.querySelectorAll('.mdc-text-field'));
textFieldElements.forEach((textFieldEl: Element) => {
    new MDCTextField(textFieldEl);
});
const dataTableElements = [].slice.call(document.querySelectorAll('.mdc-data-table'));
dataTableElements.forEach((dataTableEl: Element) => {
    new MDCDataTable(dataTableEl);
});
const topAppBarElements = [].slice.call(document.querySelectorAll('.mdc-top-app-bar'));
topAppBarElements.forEach((appBarEl: Element) => {
    new MDCTopAppBar(appBarEl);
});

const menu = new MDCMenu(document.querySelector('.mdc-menu'));
if (menu !== undefined && menu !== null)
// Add event listener to some button to toggle the menu on and off.
    document.querySelector('.language').addEventListener('click', () => menu.open = !menu.open);