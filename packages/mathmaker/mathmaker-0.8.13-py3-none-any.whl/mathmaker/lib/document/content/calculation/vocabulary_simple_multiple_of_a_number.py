# -*- coding: utf-8 -*-

# Mathmaker creates automatically maths exercises sheets
# with their answers
# Copyright 2006-2017 Nicolas Hainaux <nh.techn@gmail.com>

# This file is part of Mathmaker.

# Mathmaker is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# any later version.

# Mathmaker is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Mathmaker; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

# This module will add a question about the double|triple|quadruple of a number

from . import vocabulary_questions


class sub_object(vocabulary_questions.structure):

    def __init__(self, build_data, **options):
        # build_data must be a couple including 2, 3 or 4
        q_id = options['q_id']
        if ((q_id == 'vocabulary_double' and build_data[1] == 2)
            or (q_id == 'vocabulary_triple' and build_data[1] == 3)
            or (q_id == 'vocabulary_quadruple' and build_data[1] == 4)):
            build_data = (build_data[1], build_data[0])
        MULTIPLE_QUESTIONS = {
            'vocabulary_double': _('What is the double of {nb2}?'),
            'vocabulary_triple': _('What is the triple of {nb2}?'),
            'vocabulary_quadruple': _('What is the quadruple of {nb2}?')}
        super().__init__(build_data,
                         result_fct=lambda x, y: x * y,
                         wording=MULTIPLE_QUESTIONS[q_id],
                         shuffle_nbs=False)
