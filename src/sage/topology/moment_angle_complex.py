r"""
Moment-angle complexes

AUTHORS:

- Ognjen Petrov (2023-06-25)

This module implements the basic structure of moment-angle complexes.
Given a simplicial complex `K`, with a set of vertices
`V = \{v_1, v_2, \dotso, v_n\}`, a moment-angle complex over `K` is a
topological space `Z`, which is a union of `X_{\sigma}`, where
`\sigma \in K`, and `X_{\sigma} = Y_{v_1} \times Y_{v_2} \times \dotso \times Y_{v_n}`
and `Y_{v_i}` is a 2-disk (a 2-simplex) if `v_i \in \sigma`, or a 1-sphere otherwise.

.. MATH::

    Y_{v_i} =
    \begin{cases}
        D^2, &v_i \in \sigma\\
        S^1, &v_i \notin \sigma
    \end{cases}

.. NOTE::

    The mentioned union is not a disjoint union of topological spaces. The unit disks
    and the unit spheres are considered subsets of `\CC`, so the union is just
    a normal union of subsets of `\CC^n`.

They are one of the main topics of resarch in fields such as algebraic and
toric topology, as well as combinatorial algebraic geometry.

Here we moment-angle complexes as cubical complexes and try to compute mostly
things which would not require computing the moment-angle complex itself,
but rather work with the corresponding simplicial complex.

.. NOTE::

    One of the more useful properties will be the
    :meth:`bigraded Betti numbers<sage.topology.simplicial_complex.bigraded_betti_numbers>`,
    and the underlying theorem which makes this possible is Hochter's formula, which
    can be found on page 104 of :arxiv:`Toric topoloogy<1210.2368>`.

EXAMPLES::

    sage: MomentAngleComplex([[1,2,3], [2,4], [3,4]])
    Moment-angle complex over a simplicial complex with vertex set (1, 2, 3, 4) and facets {(2, 4), (3, 4), (1, 2, 3)}
    sage: X = SimplicialComplex([[0,1], [1,2], [1,3], [2,3]])
    sage: Z = MomentAngleComplex(X); Z
    Moment-angle complex over a simplicial complex with vertex set (0, 1, 2, 3) and facets {(0, 1), (1, 2), (1, 3), (2, 3)}
    sage: M = MomentAngleComplex([[1], [2]]); M
    Moment-angle complex over a simplicial complex with vertex set (1, 2) and facets {(1,), (2,)}

We can perform a number of operations, such as find the dimension or compute the homology::

    sage: M.homology()
    {0: 0, 1: 0, 2: 0, 3: Z}
    sage: Z.dimension()
    6
    sage: Z.homology()
    {0: 0, 1: 0, 2: 0, 3: Z x Z, 4: Z, 5: Z, 6: Z}
"""

# ****************************************************************************
#       Copyright (C) 2013 Ognjen Petrov <ognjenpetrov@yahoo.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#                  https://www.gnu.org/licenses/
# ****************************************************************************

from sage.misc.cachefunc import cached_method
from sage.homology.homology_group import HomologyGroup
from sage.rings.integer_ring import ZZ
from sage.rings.rational_field import QQ
from sage.structure.sage_object import SageObject
from sage.structure.unique_representation import UniqueRepresentation
from .cubical_complex import CubicalComplex, cubical_complexes
from .simplicial_complex import SimplicialComplex, copy
from .simplicial_complex_examples import Sphere, Simplex
from itertools import combinations

#TODO's:
# - Documentation (examples and tests)
# - add literature and references to bibliography!!!
# - add latex_name parameter?
# - add moment_angle_complex to simplicial_complex
# - add a method simplicial_complex()?
# - use different UniqueRepresentation complexes for components?


#Future TODO's:
# - explicitly state the vertices for construction
# - polyhedral products and real moment-angle complexes
# - golod decomposition
# - return for odd dimensional simplicial complexes in golod_decomposition?

# maybe make private?
def union(c1, c2):
    """
    Return the union of cubical complexes.

    This method returns a cubical complex whose set of maximal faces
    is the union of sets of maximal faces of ``c1`` and ``c2``.

    INPUT:

    - ``c1`` -- a cubical complex

    - ``c2`` -- a cubical complex

    OUTPUT: the union of cubical complexes ``c1`` and ``c2``

    .. WARNING::

        This is regular union, not disjoint union. One should be careful
        with the nomenclature of the vertices.

    EXAMPLES::

        sage: from sage.topology.moment_angle_complex import union
        sage: C1 = CubicalComplex([([0,0], [2,3]), ([0,1], [3,3]), ([0,1], [2,2]), ([1,1], [2,3])]); C1
        Cubical complex with 4 vertices and 8 cubes
        sage: C2 = CubicalComplex([([0,0], [2,3]), ([0,1], [3,3]), ([0,1], [2,2]), ([2,2], [2,3])]); C2
        Cubical complex with 6 vertices and 10 cubes
        sage: union(C1, C2)
        Cubical complex with 6 vertices and 11 cubes
        sage: union(C1, C1) == C1
        True
    """
    facets = []
    for f in c1.maximal_cells():
        facets.append(f)
    for f in c2.maximal_cells():
        facets.append(f)
    return CubicalComplex(facets)

class MomentAngleComplex(SageObject, UniqueRepresentation):
    r"""
    Define a moment-angle complex.

    INPUT:

    - ''simplicial_complex'' -- an instance of ''SimplicialComplex'',
      or an object from which an instance of ''SimplicialComplex'' can be
      created (e.g., list of facets), which represents the associated
      simplicial complex over which this moment-angle complex is created.

    EXAMPLES:

    If the associated simplicial_complex is an `n`-simplex, then the
    corresponding moment-angle complex is a polydisc (a complex ball) of
    complex dimension `n+1`::

        sage: Z = MomentAngleComplex([[0, 1, 2]]); Z
        Moment-angle complex over a simplicial complex with vertex set (0, 1, 2) and facets {(0, 1, 2)}

    This can be seen by viewing the components used in the construction
    of this moment-angle complex by calling ``components()``::

        sage: Z.components()
        {(0, 1, 2): [The 2-simplex, The 2-simplex, The 2-simplex]}

    If the associated simplicial_complex is a disjoint union of 2 points,
    then the corresponding moment-angle complex is homeomorphic to a boundary
    of a 3-sphere::

        sage: Z = MomentAngleComplex([[0], [1]]); Z
        Moment-angle complex over a simplicial complex with vertex set (0, 1) and facets {(0,), (1,)}
        sage: dict(sorted(Z.components().items()))
        {(0,): [The 2-simplex, Minimal triangulation of the 1-sphere],
         (1,): [Minimal triangulation of the 1-sphere, The 2-simplex]}

    The moment-angle complex passes all the tests of the test suite relative
    to its category::

        sage: TestSuite(Z).run()
    """

    def __init__(self, simplicial_complex):
        """
        Define a moment-angle complex. See :class:`MomentAngleComplex`
        for full documentation.

        TESTS::

            sage: Z = MomentAngleComplex([[0,1,2], [1,2,3], [0, 3]])
            sage: Z
            Moment-angle complex over a simplicial complex with vertex set (0, 1, 2, 3) and facets {(0, 3), (0, 1, 2), (1, 2, 3)}
            sage: dim(Z)
            7
            sage: TestSuite(Z).run()
        """
        # The underlying simplicial complex
        self._simplicial_complex = copy(simplicial_complex)
        # The moment-angle complex as a cubical complex
        # if create_complex() is called, this is computed
        self._moment_angle_complex = None
        # A dictionary of components indexed by facets
        self._components = {}

        vertices = self._simplicial_complex.vertices()
        # it suffices to perform union only over facets
        for facet in self._simplicial_complex.maximal_faces():
            Y = []
            for j in vertices:
                if j in facet:
                    Y.append(Simplex(2))
                else:
                    Y.append(Sphere(1))

            self._components[facet] = Y

    @staticmethod
    def __classcall_private__(cls, simplicial_complex):
        """
        TESTS::

            sage: MomentAngleComplex([[0,2], [1,2,3]]) is MomentAngleComplex([[0,2], [1,2,3]])
            True
            sage: Z = MomentAngleComplex([[0,2], [1,2,3]])
            sage: Z is MomentAngleComplex(Z)
            True
        """
        if simplicial_complex:
            if isinstance(simplicial_complex, MomentAngleComplex):
                # Allows for copy constructor
                immutable_complex = SimplicialComplex(simplicial_complex._simplicial_complex, is_mutable=False)
            elif not isinstance(simplicial_complex, SimplicialComplex):
                # Try to create a SimplicialComplex out of simplicial_complex
                # in case that simplicial_complex is a list of facets, or
                # something that can generate a SimplicialComplex
                immutable_complex = SimplicialComplex(simplicial_complex, is_mutable=False)
            elif simplicial_complex.is_mutable():
                immutable_complex = SimplicialComplex(simplicial_complex, is_mutable=False)
            else:
                immutable_complex = simplicial_complex
        else:
            immutable_complex = SimplicialComplex(is_mutable=False)
        return super().__classcall__(cls, immutable_complex)
        #behaviour for MomentAngleComplex()? maybe allow for simplexes?

    def _repr_(self):
        """
        Return a string representation of this moment-angle complex.

        TESTS::

            sage: Z = MomentAngleComplex([[0,1], [1,2], [2,0]])
            sage: Z._repr_()
            'Moment-angle complex over a simplicial complex with vertex set (0, 1, 2) and facets {(0, 1), (0, 2), (1, 2)}'
            sage: repr(Z)  # indiredt doctest
            'Moment-angle complex over a simplicial complex with vertex set (0, 1, 2) and facets {(0, 1), (0, 2), (1, 2)}'
            sage: Z  # indirect doctest
            Moment-angle complex over a simplicial complex with vertex set (0, 1, 2) and facets {(0, 1), (0, 2), (1, 2)}
            sage: Z = MomentAngleComplex([[i for i in range(20)]])
            sage: Z._repr_()
            'Moment-angle complex over a simplicial complex with 20 vertices and 1 facets'
        """
        return "Moment-angle complex over a " + self._simplicial_complex._repr_().lower()

    @cached_method
    def _create_complex(self):
        """
        Create the moment-angle complex as a cubical complex.

        If this method is called, we also explicitly compute the
        moment-angle complex, viewed as a cubical complex.

        .. WARNING::

            The construction can be very slow, it is not reccomended unless
            the corresponding simplicial complex has 5 or less vertices.

        TESTS::

            sage: Z = MomentAngleComplex([[0], [1], [2]]); Z
            Moment-angle complex over a simplicial complex with vertex set (0, 1, 2) and facets {(0,), (1,), (2,)}
            sage: Z._create_complex()
            sage: Z._moment_angle_complex
            Cubical complex with 64 vertices and 705 cubes

        This method is used in the ``cubical_complex()`` method::

            sage: Z.cubical_complex()
            Cubical complex with 64 vertices and 705 cubes
            sage: Z.cubical_complex() == Z._moment_angle_complex
            True
        """
        n = len(self._simplicial_complex.vertices())
        D = [cubical_complexes.Cube(2)] * n
        S = [cubical_complexes.Sphere(1)] * n

        self._moment_angle_complex = CubicalComplex()
        for component in self._components.values():
            x = D[0] if component[0] == Simplex(2) else S[0]
            for j in range(1, len(component)):
                y = D[j] if component[j] == Simplex(2) else S[j]
                x = x.product(y)

            self._moment_angle_complex = union(self._moment_angle_complex, x)

    def cubical_complex(self):
        """
        Return the cubical complex which represents this moment-angle complex.

        This method returns returns a cubical complex which is
        derived by explicitly computing products and unions in the
        definition of a moment-angle complex.

        .. WARNING::

            The construction can be very slow, it is not reccomended unless
            the corresponding simplicial complex has 5 or less vertices.

        EXAMPLES::

            sage: Z = MomentAngleComplex([[0,1,2], [1,2,3]]); Z
            Moment-angle complex over a simplicial complex with vertex set (0, 1, 2, 3) and facets {(0, 1, 2), (1, 2, 3)}
            sage: Z.cubical_complex()
            Cubical complex with 256 vertices and 6481 cubes
            sage: dim(Z.cubical_complex()) == dim(Z)
            True

        We can now work with moment-angle complexes as concrete cubical complexes.
        Though, it can be very slow, due to the size of the complex. However,
        for some smaller moment-angle complexes, this may be possible::

            sage: Z = MomentAngleComplex([[0], [1]]); Z
            Moment-angle complex over a simplicial complex with vertex set (0, 1) and facets {(0,), (1,)}
            sage: Z.cubical_complex().f_vector()
            [1, 16, 32, 24, 8]
        """
        if self._moment_angle_complex:
            # We check whether it has aready been created
            return self._moment_angle_complex
        else:
            self._create_complex()
            return self._moment_angle_complex

    def components(self):
        """
        Return the dictionary of components of ``self``, indexed by facets
        of the associated simplicial complex.

        OUTPUT:

        - a dictonary, whose values are lists, representing spheres
          and disks described in the construction of the moment-angle
          complex. ``The 2-simplex`` represents a disk, and
          ``Minimal triangulation of the 1-sphere`` represents a `1-sphere`.

        EXAMPLES::

            sage: M = MomentAngleComplex([[0, 1, 2]]); M
            Moment-angle complex over a simplicial complex with vertex set (0, 1, 2) and facets {(0, 1, 2)}
            sage: M.components()
            {(0, 1, 2): [The 2-simplex, The 2-simplex, The 2-simplex]}
            sage: Z = MomentAngleComplex([[0,1], [1,2], [2,3], [3,0]])
            sage: dict(sorted(Z.components().items()))
            {(0, 1): [The 2-simplex,
              The 2-simplex,
              Minimal triangulation of the 1-sphere,
              Minimal triangulation of the 1-sphere],
             (0, 3): [The 2-simplex,
              Minimal triangulation of the 1-sphere,
              Minimal triangulation of the 1-sphere,
              The 2-simplex],
             (1, 2): [Minimal triangulation of the 1-sphere,
              The 2-simplex,
              The 2-simplex,
              Minimal triangulation of the 1-sphere],
             (2, 3): [Minimal triangulation of the 1-sphere,
              Minimal triangulation of the 1-sphere,
              The 2-simplex,
              The 2-simplex]}

        It is not that difficult to prove that the previous moment-angle complex
        is homeomorphic to a product of two 3-spheres. We can look at the
        cohomologies to try and validate whether this makes sense::

            sage: from sage.topology.simplicial_complex_examples import Sphere as S
            sage: product_of_spheres = S(3).product(S(3))
            sage: Z.cohomology()
            {0: 0, 1: 0, 2: 0, 3: Z x Z, 4: 0, 5: 0, 6: Z}
            sage: Z.cohomology() == product_of_spheres.cohomology()
            True
        """
        return self._components

    def dimension(self):
        r"""
        The dimension of this moment-angle complex.

        The dimension of a moment-angle complex is the dimension
        of the constructed (cubical) complex. It is not difficult to
        see that this turns out to be `m+n+1`, where `m` is the number
        of vertices and `n` is the dimension of the associated simplicial
        complex.

        EXAMPLES::

            sage: Z = MomentAngleComplex([[0,1], [1,2,3]])
            sage: Z.dimension()
            7
            sage: Z = MomentAngleComplex([[0, 1, 2]])
            sage: Z.dimension()
            6
            sage: dim(Z)  # indirect doctest
            6

        We can construct the cubical complex and compare whether
        the dimensions coincide::

            sage: dim(Z) == dim(Z.cubical_complex())
            True
        """
        number_of_vertices = len(self._simplicial_complex.vertices())
        dim = self._simplicial_complex.dimension()
        return number_of_vertices + dim + 1

    def trivial_massey_product(self):
        """
        Return whether ``self`` has a non-trivial Massey product.

        This is the Massey product in the cohomology of the
        moment-angle complex.

        EXAMPLES::

        <Lots and lots of examples>
        """
        from sage.graphs.graph import Graph

        one_skeleton = self._simplicial_complex.graph()

        obstruction_graphs = [
            Graph([(1, 2), (1, 4), (2, 3), (3, 5), (5, 6), (4, 5), (1, 6)]),
            Graph([(1, 2), (1, 4), (2, 3), (3, 5), (5, 6), (4, 5), (1, 6), (2, 6)]),
            Graph([(1, 2), (1, 4), (2, 3), (3, 5), (5, 6), (4, 5), (1, 6), (4, 6)]),
            Graph([(1, 2), (1, 4), (2, 3), (3, 5), (5, 6), (4, 5), (1, 6), (2, 6), (4, 6)]),
            Graph([(1, 2), (1, 4), (2, 3), (3, 5), (5, 6), (3, 4), (2, 6), (1, 6), (4, 5)]),
            Graph([(1, 2), (1, 4), (2, 3), (3, 5), (5, 6), (3, 4), (2, 6), (1, 6), (4, 5), (4, 6)]),
            Graph([(1, 2), (1, 4), (2, 3), (3, 5), (5, 6), (3, 4), (2, 6), (4, 5), (4, 6)]),
            Graph([(1, 2), (1, 4), (2, 3), (3, 5), (5, 6), (3, 4), (2, 6), (4, 6)]),
        ]

        return not any(one_skeleton.subgraph_search(g) is not None for g in obstruction_graphs)

    #needs work
    def golod_decomposition(self):
        """
        Determine whether ``self`` can be written (is homeomorphic) to a
        connected sum of sphere products, with two spheres in each product.

        This is done by checking the dimension and minimal non-Golodness of
        the associated simplicial complex.

        EXAMPLES::

        <Lots and lots of examples>
        """
        if self._simplicial_complex.dimension() % 2 != 0 or not self._simplicial_complex.is_minimally_non_golod():
            return False
            # or maybe NotImplementedError?

        B = self._simplicial_complex.bigraded_betti_numbers()
        x = {(B.get((a, b)), a+b) for (a, b) in B}
        D = {a : [] for (a, b) in x}
        for (a, b) in x:
            D[a].append(b)

        D.pop(1)

        out = ""
        for num in D:
            c1 = "S^" + str(D[num][0])
            if len(D[num]) == 1:
                c2 = " x " + c1
            for i in range(1, len(D[num])):
                c2 = " x S^" + str(D[num][i])

            out = out + " #(" + c1 + c2 + ")^" + str(num)
        # needs work
        return out

    @cached_method # maybe ignore the algorithm?
    def _homology_group(self, l, base_ring=ZZ, cohomology=False,
                     algorithm='pari', verbose=False, reduced=True):
        """
        The `l`-th (reduced) homology group of this moment-angle complex.

        INPUT:

        - ``l`` -- integer; index of the homology group which
          we want to compute

        - ``base_ring`` -- commutative ring, must be ``ZZ`` or a field.
          It is optional, the default is ``ZZ``

        - ``cohomology`` -- boolean; optional, is ``False`` by default.
          If ``True``, compute cohomology rather than homology.

        - ``algorithm`` -- a string which represents the method for
          computing homology. The options are 'auto', 'dhsw', or 'pari'.
          See below for a description of what they mean.

        - ``verbose`` -- boolean; optional, is ``False`` by default.
          If ``True``, print some messages as the homology is computed.

        - ``reduced`` -- boolean; optional, is ``True`` by default.
          If ``True``, return the reduced homology.

        ALGORITHM:

        This algorithm is adopted from theorem 4.5.8. on page 154 of
        :arxiv:`Toric topoloogy<1210.2368>`.

        The (co)homology of the moment-angle complex is closely related
        to the (co)homologies of certain full subcomplexes of the
        associated simplicial complex. For more information, see the
        theorem mentioned above. We find those subcomplexes, and then
        we compute their (co)homologies with the parsed arguments.

        .. SEEALSO::

            :meth:`sage.topology.moment_angle_complex.homology`,
            :meth:`sage.topology.cell_complex.homology`.

        TESTS::

            sage: Z = MomentAngleComplex([[0,1,2], [1,2,3]]); Z
            Moment-angle complex over a simplicial complex with vertex set (0, 1, 2, 3) and facets {(0, 1, 2), (1, 2, 3)}
            sage: Z._homology_group(3)
            Z
            sage: Z._homology_group(4)
            0
            sage: Z.homology()
            {0: 0, 1: 0, 2: 0, 3: Z, 4: 0, 5: 0, 6: 0, 7: 0}
            sage: RP = simplicial_complexes.RealProjectivePlane()
            sage: Z = MomentAngleComplex(RP)
            sage: Z._homology_group(8)
            C2

        This yields the same result as creating a cubical complex
        from this moment-angle complex, and then computing its (co)homology,
        but that is incomparably slower and is really only possible when
        the associated simplicial complex is very small::

            sage: Z = MomentAngleComplex([[0,1], [1,2], [2,0]]); Z
            Moment-angle complex over a simplicial complex with vertex set (0, 1, 2) and facets {(0, 1), (0, 2), (1, 2)}
            sage: Z.cubical_complex()
            Cubical complex with 64 vertices and 729 cubes
            sage: Z.cubical_complex().homology(5) == Z._homology_group(5)
            True
        """
        vertices = self._simplicial_complex.vertices()
        n = len(vertices)
        invfac = []

        for j in range(n+1):
            for x in combinations(vertices, j):
                S = self._simplicial_complex.generated_subcomplex(x)
                if base_ring.is_field():
                    invfac.append(S.homology(l-j-1, base_ring=base_ring,
                                             cohomology=cohomology, algorithm=algorithm,
                                             verbose=verbose, reduced=reduced).dimension())
                else:
                    invfac.extend(S.homology(l-j-1, base_ring=base_ring,
                                             cohomology=cohomology, algorithm=algorithm,
                                             verbose=verbose, reduced=reduced)._original_invts)

        if base_ring.is_field():
            return HomologyGroup(sum(invfac), base_ring)

        m = len(invfac)
        return HomologyGroup(m, base_ring, invfac)

    def homology(self, dim=None, base_ring=ZZ, cohomology=False,
                 algorithm='pari', verbose=False, reduced=True):
        """
        The (reduced) homology of this moment-angle complex.

        INPUT:

        - ``dim`` -- integer, or a list of integers; Represents the
          homology (or homologies) we want to compute

        - ``base_ring`` -- commutative ring, must be ``ZZ`` or a field.
          It is optional, the default is ``ZZ``

        - ``cohomology`` -- boolean; optional, is ``False`` by default.
          If ``True``, compute cohomology rather than homology.

        - ``algorithm`` -- a string which represents the method for
          computing homology. The options are 'auto', 'dhsw', or 'pari'.
          See below for a description of what they mean.

        - ``verbose`` -- boolean; optional, is ``False`` by default.
          If ``True``, print some messages as the homology is computed.

        - ``reduced`` -- boolean; optional, is ``True`` by default.
          If ``True``, return the reduced homology.

        ALGORITHM:

        This algorithm is adopted from theorem 4.5.8. on page 154 of
        :arxiv:`Toric topoloogy<1210.2368>`.

        The (co)homology of the moment-angle complex is closely related
        to the (co)homologies of certain full subcomplexes of the
        associated simplicial complex. For more information, see the
        theorem mentioned above. We find those subcomplexes, and then
        we compute their (co)homologies with the parsed arguments.

        .. SEEALSO::

            :meth:`sage.topology.cell_complex.homology`.

        EXAMPLES::

            sage: Z = MomentAngleComplex([[0,1,2], [1,2,3], [3,0]]); Z
            Moment-angle complex over a simplicial complex with vertex set (0, 1, 2, 3) and facets {(0, 3), (0, 1, 2), (1, 2, 3)}
            sage: Z = MomentAngleComplex([[0,1,2], [1,2,3], [3,0]])
            sage: Z.homology()
            {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: Z x Z, 6: Z, 7: 0}
            sage: Z.homology(base_ring=GF(2))
            {0: Vector space of dimension 0 over Finite Field of size 2,
             1: Vector space of dimension 0 over Finite Field of size 2,
             2: Vector space of dimension 0 over Finite Field of size 2,
             3: Vector space of dimension 0 over Finite Field of size 2,
             4: Vector space of dimension 0 over Finite Field of size 2,
             5: Vector space of dimension 2 over Finite Field of size 2,
             6: Vector space of dimension 1 over Finite Field of size 2,
             7: Vector space of dimension 0 over Finite Field of size 2}
           sage: RP = simplicial_complexes.RealProjectivePlane()
           sage: Z = MomentAngleComplex(RP)
           sage: Z.homology()
           {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: Z^10, 6: Z^15, 7: Z^6, 8: C2, 9: 0}

        This yields the same result as creating a cubical complex
        from this moment-angle complex, and then computing its (co)homology,
        but that is incomparably slower and is really only possible when
        the associated simplicial complex is very small::

            sage: Z = MomentAngleComplex([[0,1], [1,2], [2,0]]); Z
            Moment-angle complex over a simplicial complex with vertex set (0, 1, 2) and facets {(0, 1), (0, 2), (1, 2)}
            sage: Z.cubical_complex()
            Cubical complex with 64 vertices and 729 cubes
            sage: Z.cubical_complex().homology() == Z.homology()
            True

        Meanwhile, the homology computation used here is quite efficient
        and works well even with significantly larger underlying simplicial
        complexes::

            sage: Z = MomentAngleComplex([[0,1,2,3,4,5], [0,1,2,3,4,6], [0,1,2,3,5,7], [0,1,2,3,6,8,9]])
            sage: Z.homology()
            {0: 0,
             1: 0,
             2: 0,
             3: Z^9,
             4: Z^17,
             5: Z^12,
             6: Z x Z x Z,
             7: 0,
             8: 0,
             9: 0,
             10: 0,
             11: 0,
             12: 0,
             13: 0,
             14: 0,
             15: 0,
             16: 0,
             17: 0}
        """
        if dim is not None:
            if isinstance(dim, (list, tuple, range)):
                low = min(dim)
                high = max(dim)
            else:
                low = dim
                high = dim
            dims = range(low, high + 1)
        else:
            dims = range(self.dimension()+1)

        answer = {i : self._homology_group(i, base_ring=base_ring,
                                             cohomology=cohomology, algorithm=algorithm,
                                             verbose=verbose, reduced=reduced) for i in dims}
        return answer

    def cohomology(self, dim=None, base_ring=ZZ, algorithm='pari',
                 verbose=False, reduced=True):
        r"""
        The reduced cohomology of this moment-angle complex.

        This is equivalent to calling the ``homology()`` method,
        with ``cohomology=True`` as an argument.

        .. SEEALSO::

            :meth:`sage.topology.moment_angle_complex.homology`.

        EXAMPLES::

            sage: X = SimplicialComplex([[0,1],[1,2],[2,3],[3,0]])  # an empty square
            sage: Z = MomentAngleComplex(X)

        It is known that the previous moment-angle complex is homeomorphic
        to a product of two 3-spheres (which can be seen by looking at the
        output of ``components()``).

            sage: from sage.topology.simplicial_complex_examples import Sphere as S
            sage: product_of_spheres = S(3).product(S(3))
            sage: Z.cohomology()
            {0: 0, 1: 0, 2: 0, 3: Z x Z, 4: 0, 5: 0, 6: Z}
            sage: Z.cohomology() == product_of_spheres.cohomology()
            True
        """
        return self.homology(dim=dim, cohomology=True, base_ring=base_ring,
                             algorithm=algorithm, verbose=verbose, reduced=reduced)

    def betti(self, dim=None):
        r"""
        The Betti numbers of this moment-angle complex as a dictionary
        (or a single Betti number, if only one dimension is given):
        the ith Betti number is the rank of the ith homology group.

        :param dim: If ``None``, then return every Betti number, as
           a dictionary with keys the non-negative integers.  If
           ``dim`` is an integer or list, return the Betti number for
           each given dimension.  (Actually, if ``dim`` is a list,
           return the Betti numbers, as a dictionary, in the range
           from ``min(dim)`` to ``max(dim)``.  If ``dim`` is a number,
           return the Betti number in that dimension.)
        :type dim: integer or list of integers or ``None``; optional,
           default ``None``

        EXAMPLES::

        <Lots and lots of examples>
        """
        dict = {}
        H = self.homology(dim=dim, base_ring=QQ)
        try:
            for n in H.keys():
                dict[n] = H[n].dimension()
                if n == 0:
                    dict[n] += 1
            return dict
        except AttributeError:
            return H.dimension()

    def euler_characteristic(self):
        """
        Return the Euler characteristic of ``self``.

        EXAMPLES::

        <Lots and lots of examples>
        """
        return sum([(-1)**n * self.betti()[n] for n in range(self.dimension() + 1)])

    def product(self, other):
        """
        The product of this moment-angle complex with another one.

        It is known that the product of two moment-angle complexes
        is a moment-angle complex over the join of the two corresponding
        simplicial complexes.

        EXAMPLES::

        <Lots and lots of examples>
        """
        simplicial_complex = self._simplicial_complex.join(other._simplicial_complex, rename_vertices=True)
        return MomentAngleComplex(simplicial_complex)
