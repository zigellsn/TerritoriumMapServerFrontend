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

let mix = require('laravel-mix');

mix.disableNotifications()
    .setPublicPath('./TerritoriumMapServerFrontend/static/')
    .ts('./mdc/init_mdc.ts', 'js/bundle.js');

let src = ['./node_modules/htmx.org/dist/htmx.min.js',
    './node_modules/htmx-ext-ws/ws.js',
    './node_modules/luxon/build/global/luxon.min.js',
    './TerritoriumMapServerFrontend/static/js/bundle.js',
    './node_modules/hyperscript.org/dist/_hyperscript.min.js'];

if (process.env.NODE_ENV === 'development')
    src.push('./node_modules/hyperscript.org/src/hdb.js');

mix.combine(src, './TerritoriumMapServerFrontend/static/js/bundle.js')
    .sass('./mdc/mdc.scss', 'css/bundle.css')
    .combine(['./TerritoriumMapServerFrontend/static/css/bundle.css', './node_modules/normalize.css/normalize.css'],
        'css/bundle.css');
