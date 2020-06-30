..
    Copyright 2017-2020 - Swiss Data Science Center (SDSC)
    A partnership between École Polytechnique Fédérale de Lausanne (EPFL) and
    Eidgenössische Technische Hochschule Zürich (ETHZ).

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.

Changes
=======

`0.3.0 <https://github.com/SwissDataScienceCenter/calamus/compare/v0.2.0...v0.3.0>`__ (2020-06-30)
--------------------------------------------------------------------------------------------------

Features
~~~~~~~~

- Added lazy loading support
  (`#12 <https://github.com/SwissDataScienceCenter/calamus/issues/12>`__)


`0.2.0 <https://github.com/SwissDataScienceCenter/calamus/compare/v0.1.2...v0.2.0>`__ (2020-05-08)
--------------------------------------------------------------------------------------------------

Features
~~~~~~~~

- Added IRIField
  (`#24 <https://github.com/SwissDataScienceCenter/calamus/pull/24>`__)

- Added BooleanField
  (`1a93bdd <https://github.com/SwissDataScienceCenter/calamus/commit/1a93bdd1cdb6478b7c3a6a17e9ad803df1e0ca39>`__)

- Added ``init_name`` setting to fields for cases where the name of the property differs from the name in the
  ``__init__`` method

Fixes
~~~~~
- Fixed an issue where ``fields.Nested`` would not work when used inside ``fields.List``



`0.1.2 <https://github.com/SwissDataScienceCenter/calamus/compare/v0.1.1...v0.1.2>`__ (2020-05-08)
--------------------------------------------------------------------------------------------------

Features
~~~~~~~~

- Allow serializing to a flat list
  (`#5 <https://github.com/SwissDataScienceCenter/calamus/issues/5>`__)
  (`4289d86 <https://github.com/SwissDataScienceCenter/calamus/commit/4289d8632a346d636192926a16805b202d3c906a>`__)

- Allow deserializing from a flat list
  (`#4 <https://github.com/SwissDataScienceCenter/calamus/issues/4>`__)
  (`e8d56b3 <https://github.com/SwissDataScienceCenter/calamus/commit/e8d56b3a4b48c92bd117bde002c104a3a8ef7451>`__)



`0.1.1 <https://github.com/SwissDataScienceCenter/calamus/tree/v0.1.1>`__ (2020-05-01)
--------------------------------------------------------------------------------------------------

Features
~~~~~~~~

- Initial public release of calamus.
