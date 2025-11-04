#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
文件描述:  主要修复 无主键查询中 语句中的总是携带 主表 主键的问题  :89行
作者: 李辉
创建日期: 2025-11-03
版本号: 1.0.0
最后修改: 2025-11-03
"""


from itertools import chain

import django
from django.db.models.expressions import Ref
from django.db.models.functions import  Random
from django.db.transaction import TransactionManagementError
from django.db.utils import NotSupportedError
if django.VERSION >= (3, 1):
    from django.db.models.fields.json import compile_json_path, KeyTransform as json_KeyTransform
if django.VERSION >= (4, 2):
    from django.core.exceptions import EmptyResultSet, FullResultSet
from django.db.models  import sql 
from django.db import models
from mssql import compiler

class AnnotateSQLCompiler(compiler.SQLCompiler):

    def as_sql(self, with_limits=True, with_col_aliases=False):
        """
        主要修复 无主键查询中 语句中的总是携带 主表 主键的问题  :89行
        """
        refcounts_before = self.query.alias_refcount.copy()
        try:
            extra_select, order_by, group_by = self.pre_sql_setup()
            for_update_part = None
            # Is a LIMIT/OFFSET clause needed?
            with_limit_offset = with_limits and (self.query.high_mark is not None or self.query.low_mark)
            combinator = self.query.combinator
            features = self.connection.features

            # The do_offset flag indicates whether we need to construct
            # the SQL needed to use limit/offset w/SQL Server.
            high_mark = self.query.high_mark
            low_mark = self.query.low_mark
            do_limit = with_limits and high_mark is not None
            do_offset = with_limits and low_mark != 0
            # SQL Server 2012 or newer supports OFFSET/FETCH clause
            supports_offset_clause = self.connection.sql_server_version >= 2012
            do_offset_emulation = do_offset and not supports_offset_clause

            if combinator:
                if not getattr(features, 'supports_select_{}'.format(combinator)):
                    raise NotSupportedError('{} is not supported on this database backend.'.format(combinator))
                result, params = self.get_combinator_sql(combinator, self.query.combinator_all)
            elif django.VERSION >= (4, 2) and self.qualify:
                result, params = self.get_qualify_sql()
                order_by = None
            else:
                distinct_fields, distinct_params = self.get_distinct()
                # This must come after 'select', 'ordering', and 'distinct' -- see
                # docstring of get_from_clause() for details.
                from_, f_params = self.get_from_clause()
                if django.VERSION >= (4, 2):
                    try:
                        where, w_params = self.compile(self.where) if self.where is not None else ("", [])
                    except EmptyResultSet:
                        if self.elide_empty:
                            raise
                        # Use a predicate that's always False.
                        where, w_params = "0 = 1", []
                    except FullResultSet:
                        where, w_params = "", []
                    try:
                        having, h_params = self.compile(self.having) if self.having is not None else ("", [])
                    except FullResultSet:
                        having, h_params = "", []
                else:
                    where, w_params = self.compile(self.where) if self.where is not None else ("", [])
                    having, h_params = self.compile(self.having) if self.having is not None else ("", [])
                params = []
                result = ['SELECT']

                if self.query.distinct:
                    distinct_result, distinct_params = self.connection.ops.distinct_sql(
                        distinct_fields,
                        distinct_params,
                    )
                    result += distinct_result
                    params += distinct_params

                # SQL Server requires the keword for limitting at the begenning
                if do_limit and not do_offset:
                    result.append('TOP %d' % high_mark)

                out_cols = []
                col_idx = 1
                for _, (s_sql, s_params), alias in self.select + extra_select:
                    if alias:
                        s_sql = '%s AS %s' % (s_sql, self.connection.ops.quote_name(alias))
                    elif with_col_aliases or do_offset_emulation:
                        s_sql = '%s AS %s' % (s_sql, 'Col%d' % col_idx)
                        col_idx += 1
                    params.extend(s_params)
                    out_cols.append(s_sql)

                # SQL Server requires an order-by clause for offsetting
                if do_offset:
                    meta = self.query.get_meta()
                    qn = self.quote_name_unless_alias
                    # offsetting_order_by='ROW_NUMBER () OVER ( ORDER BY (SELECT NULL )) AS [rn] '
                    offsetting_order_by = f'(SELECT NULL)'#,'%s.%s' % (qn(meta.db_table), qn(meta.pk.db_column or meta.pk.column))
                    if do_offset_emulation:
                        if order_by:
                            ordering = []
                            for expr, (o_sql, o_params, _) in order_by:
                                # value_expression in OVER clause cannot refer to
                                # expressions or aliases in the select list. See:
                                # http://msdn.microsoft.com/en-us/library/ms189461.aspx
                                src = next(iter(expr.get_source_expressions()))
                                if isinstance(src, Ref):
                                    src = next(iter(src.get_source_expressions()))
                                    o_sql, _ = src.as_sql(self, self.connection)
                                    odir = 'DESC' if expr.descending else 'ASC'
                                    o_sql = '%s %s' % (o_sql, odir)
                                ordering.append(o_sql)
                                params.extend(o_params)
                            offsetting_order_by = ', '.join(ordering)
                            order_by = []
                        out_cols.append('ROW_NUMBER() OVER (ORDER BY %s) AS [rn]' % offsetting_order_by)
                    elif not order_by:
                        order_by.append(((None, ('%s ASC' % offsetting_order_by, [], None))))

                if self.query.select_for_update and self.connection.features.has_select_for_update:
                    if self.connection.get_autocommit():
                        raise TransactionManagementError('select_for_update cannot be used outside of a transaction.')

                    if with_limit_offset and not self.connection.features.supports_select_for_update_with_limit:
                        raise NotSupportedError(
                            'LIMIT/OFFSET is not supported with '
                            'select_for_update on this database backend.'
                        )
                    nowait = self.query.select_for_update_nowait
                    skip_locked = self.query.select_for_update_skip_locked
                    of = self.query.select_for_update_of
                    # If it's a NOWAIT/SKIP LOCKED/OF query but the backend
                    # doesn't support it, raise NotSupportedError to prevent a
                    # possible deadlock.
                    if nowait and not self.connection.features.has_select_for_update_nowait:
                        raise NotSupportedError('NOWAIT is not supported on this database backend.')
                    elif skip_locked and not self.connection.features.has_select_for_update_skip_locked:
                        raise NotSupportedError('SKIP LOCKED is not supported on this database backend.')
                    elif of and not self.connection.features.has_select_for_update_of:
                        raise NotSupportedError('FOR UPDATE OF is not supported on this database backend.')
                    for_update_part = self.connection.ops.for_update_sql(
                        nowait=nowait,
                        skip_locked=skip_locked,
                        of=self.get_select_for_update_of_arguments(),
                    )

                if for_update_part and self.connection.features.for_update_after_from:
                    from_.insert(1, for_update_part)

                result += [', '.join(out_cols)]
                if from_:
                    result += ['FROM', *from_]
                params.extend(f_params)

                if where:
                    result.append('WHERE %s' % where)
                    params.extend(w_params)

                grouping = []
                for g_sql, g_params in group_by:
                    grouping.append(g_sql)
                    params.extend(g_params)
                if grouping:
                    if distinct_fields:
                        raise NotImplementedError('annotate() + distinct(fields) is not implemented.')
                    order_by = order_by or self.connection.ops.force_no_ordering()
                    result.append('GROUP BY %s' % ', '.join(grouping))

                if having:
                    result.append('HAVING %s' % having)
                    params.extend(h_params)

            explain = self.query.explain_info if django.VERSION >= (4, 0) else self.query.explain_query
            if explain:
                result.insert(0, self.connection.ops.explain_query_prefix(
                    self.query.explain_format,
                    **self.query.explain_options
                ))

            if order_by:
                ordering = []
                for expr, (o_sql, o_params, _) in order_by:
                    if expr:
                        src = next(iter(expr.get_source_expressions()))
                        if isinstance(src, Random):
                            # ORDER BY RAND() doesn't return rows in random order
                            # replace it with NEWID()
                            o_sql = o_sql.replace('RAND()', 'NEWID()')
                    ordering.append(o_sql)
                    params.extend(o_params)
                result.append('ORDER BY %s' % ', '.join(ordering))

                # For subqueres with an ORDER BY clause, SQL Server also
                # requires a TOP or OFFSET clause which is not generated for
                # Django 2.x.  See https://github.com/microsoft/mssql-django/issues/12
                # Add OFFSET for all Django versions.
                # https://github.com/microsoft/mssql-django/issues/109
                if not (do_offset or do_limit) and supports_offset_clause:
                    result.append("OFFSET 0 ROWS")

            # SQL Server requires the backend-specific emulation (2008 or earlier)
            # or an offset clause (2012 or newer) for offsetting
            if do_offset:
                if do_offset_emulation:
                    # Construct the final SQL clause, using the initial select SQL
                    # obtained above.
                    result = ['SELECT * FROM (%s) AS X WHERE X.rn' % ' '.join(result)]
                    # Place WHERE condition on `rn` for the desired range.
                    if do_limit:
                        result.append('BETWEEN %d AND %d' % (low_mark + 1, high_mark))
                    else:
                        result.append('>= %d' % (low_mark + 1))
                    if not self.query.subquery:
                        result.append('ORDER BY X.rn')
                else:
                    result.append(self.connection.ops.limit_offset_sql(self.query.low_mark, self.query.high_mark))

            if self.query.subquery and extra_select:
                # If the query is used as a subquery, the extra selects would
                # result in more columns than the left-hand side expression is
                # expecting. This can happen when a subquery uses a combination
                # of order_by() and distinct(), forcing the ordering expressions
                # to be selected as well. Wrap the query in another subquery
                # to exclude extraneous selects.
                sub_selects = []
                sub_params = []
                for index, (select, _, alias) in enumerate(self.select, start=1):
                    if not alias and with_col_aliases:
                        alias = 'col%d' % index
                    if alias:
                        sub_selects.append("%s.%s" % (
                            self.connection.ops.quote_name('subquery'),
                            self.connection.ops.quote_name(alias),
                        ))
                    else:
                        select_clone = select.relabeled_clone({select.alias: 'subquery'})
                        subselect, subparams = select_clone.as_sql(self, self.connection)
                        sub_selects.append(subselect)
                        sub_params.extend(subparams)
                return 'SELECT %s FROM (%s) subquery' % (
                    ', '.join(sub_selects),
                    ' '.join(result),
                ), tuple(sub_params + params)

            return ' '.join(result), tuple(params)
        finally:
            # Finally do cleanup - get rid of the joins we created above.
            self.query.reset_refcounts(refcounts_before)

class AggQuerySet(models.QuerySet):
    def __init__(self, model=None, query=None, using=None, hints=None):
        super().__init__(model, query, using, hints)
        _query = query or sql.Query(self.model)
        setattr(compiler,'AnnotateSQLCompiler' , AnnotateSQLCompiler)
        self.query = _query